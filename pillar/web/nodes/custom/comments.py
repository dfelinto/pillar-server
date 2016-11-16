import logging
import warnings

from flask import current_app
from flask import request
from flask import jsonify
from flask import render_template
from flask_login import login_required, current_user
from pillarsdk import Node
from pillarsdk import Project
import werkzeug.exceptions as wz_exceptions

from pillar.web import subquery
from pillar.web.nodes.routes import blueprint
from pillar.web.utils import gravatar
from pillar.web.utils import pretty_date, datetime_now
from pillar.web.utils import system_util

log = logging.getLogger(__name__)


@blueprint.route('/comments/create', methods=['POST'])
@login_required
def comments_create():
    content = request.form['content']
    parent_id = request.form.get('parent_id')

    if not parent_id:
        log.warning('User %s tried to create comment without parent_id', current_user.objectid)
        raise wz_exceptions.UnprocessableEntity()

    api = system_util.pillar_api()
    parent_node = Node.find(parent_id, api=api)
    if not parent_node:
        log.warning('Unable to create comment for user %s, parent node %r not found',
                    current_user.objectid, parent_id)
        raise wz_exceptions.UnprocessableEntity()

    log.info('Creating comment for user %s on parent node %r',
             current_user.objectid, parent_id)

    comment_props = dict(
        project=parent_node.project,
        name='Comment',
        user=current_user.objectid,
        node_type='comment',
        properties=dict(
            content=content,
            status='published',
            confidence=0,
            rating_positive=0,
            rating_negative=0))

    if parent_id:
        comment_props['parent'] = parent_id

    # Get the parent node and check if it's a comment. In which case we flag
    # the current comment as a reply.
    parent_node = Node.find(parent_id, api=api)
    if parent_node.node_type == 'comment':
        comment_props['properties']['is_reply'] = True

    comment = Node(comment_props)
    comment.create(api=api)

    return jsonify({'node_id': comment._id}), 201


@blueprint.route('/comments/<string(length=24):comment_id>', methods=['POST'])
@login_required
def comment_edit(comment_id):
    """Allows a user to edit their comment."""

    api = system_util.pillar_api()

    comment = Node({'_id': comment_id})
    result = comment.patch({'op': 'edit', 'content': request.form['content']}, api=api)
    assert result['_status'] == 'OK'

    return jsonify({
        'status': 'success',
        'data': {
            'content_html': result.properties.content_html,
        }})


def format_comment(comment, is_reply=False, is_team=False, replies=None):
    """Format a comment node into a simpler dictionary.

    :param comment: the comment object
    :param is_reply: True if the comment is a reply to another comment
    :param is_team: True if the author belongs to the group that owns the node
    :param replies: list of replies (formatted with this function)
    """
    try:
        is_own = (current_user.objectid == comment.user._id) \
            if current_user.is_authenticated else False
    except AttributeError:
        current_app.bugsnag.notify(Exception(
            'Missing user for embedded user ObjectId'),
            meta_data={'nodes_info': {'node_id': comment['_id']}})
        return
    is_rated = False
    is_rated_positive = None
    if comment.properties.ratings:
        for rating in comment.properties.ratings:
            if current_user.is_authenticated and rating.user == current_user.objectid:
                is_rated = True
                is_rated_positive = rating.is_positive
                break

    return dict(_id=comment._id,
                gravatar=gravatar(comment.user.email, size=32),
                time_published=pretty_date(comment._created or datetime_now(), detail=True),
                rating=comment.properties.rating_positive - comment.properties.rating_negative,
                author=comment.user.full_name,
                author_username=comment.user.username,
                content=comment.properties.content,
                is_reply=is_reply,
                is_own=is_own,
                is_rated=is_rated,
                is_rated_positive=is_rated_positive,
                is_team=is_team,
                replies=replies)


@blueprint.route("/comments/")
def comments_index():
    warnings.warn('comments_index() is deprecated in favour of comments_for_node()')

    parent_id = request.args.get('parent_id')
    # Get data only if we format it
    api = system_util.pillar_api()
    if request.args.get('format') == 'json':
        nodes = Node.all({
            'where': '{"node_type" : "comment", "parent": "%s"}' % (parent_id),
            'embedded': '{"user":1}'}, api=api)

        comments = []
        for comment in nodes._items:
            # Query for first level children (comment replies)
            replies = Node.all({
                'where': '{"node_type" : "comment", "parent": "%s"}' % (comment._id),
                'embedded': '{"user":1}'}, api=api)
            replies = replies._items if replies._items else None
            if replies:
                replies = [format_comment(reply, is_reply=True) for reply in replies]

            comments.append(
                format_comment(comment, is_reply=False, replies=replies))

        return_content = jsonify(items=[c for c in comments if c is not None])
    else:
        parent_node = Node.find(parent_id, api=api)
        project = Project({'_id': parent_node.project})
        has_method_POST = project.node_type_has_method('comment', 'POST', api=api)
        # Data will be requested via javascript
        return_content = render_template('nodes/custom/_comments.html',
                                         parent_id=parent_id,
                                         has_method_POST=has_method_POST)
    return return_content


@blueprint.route('/<string(length=24):node_id>/comments')
def comments_for_node(node_id):
    """Shows the comments attached to the given node."""

    api = system_util.pillar_api()

    node = Node.find(node_id, api=api)
    project = Project({'_id': node.project})
    can_post_comments = project.node_type_has_method('comment', 'POST', api=api)
    can_comment_override = request.args.get('can_comment', 'True') == 'True'
    can_post_comments = can_post_comments and can_comment_override

    # Query for all children, i.e. comments on the node.
    comments = Node.all({
        'where': {'node_type': 'comment', 'parent': node_id},
    }, api=api)

    def enrich(some_comment):
        some_comment['_user'] = subquery.get_user_info(some_comment['user'])
        some_comment['_is_own'] = some_comment['user'] == current_user.objectid
        some_comment['_current_user_rating'] = None  # tri-state boolean
        some_comment['_rating'] = some_comment.properties.rating_positive - some_comment.properties.rating_negative

        if current_user.is_authenticated:
            for rating in some_comment.properties.ratings or ():
                if rating.user != current_user.objectid:
                    continue

                some_comment['_current_user_rating'] = rating.is_positive

    for comment in comments['_items']:
        # Query for all grandchildren, i.e. replies to comments on the node.
        comment['_replies'] = Node.all({
            'where': {'node_type': 'comment', 'parent': comment['_id']},
        }, api=api)

        enrich(comment)
        for reply in comment['_replies']['_items']:
            enrich(reply)

    nr_of_comments = sum(1 + comment['_replies']['_meta']['total']
                         for comment in comments['_items'])

    return render_template('nodes/custom/comment/list_embed.html',
                           node_id=node_id,
                           comments=comments,
                           nr_of_comments=nr_of_comments,
                           show_comments=True,
                           can_post_comments=can_post_comments)


@blueprint.route('/<string(length=24):node_id>/commentform')
def commentform_for_node(node_id):
    """Shows only the comment for for comments attached to the given node.

    i.e. does not show the comments themselves, just the form to post a new comment.
    """

    api = system_util.pillar_api()

    node = Node.find(node_id, api=api)
    project = Project({'_id': node.project})
    can_post_comments = project.node_type_has_method('comment', 'POST', api=api)

    return render_template('nodes/custom/comment/list_embed.html',
                           node_id=node_id,
                           show_comments=False,
                           can_post_comments=can_post_comments)


@blueprint.route("/comments/<comment_id>/rate/<operation>", methods=['POST'])
@login_required
def comments_rate(comment_id, operation):
    """Comment rating function

    :param comment_id: the comment id
    :type comment_id: str
    :param rating: the rating (is cast from 0 to False and from 1 to True)
    :type rating: int

    """

    if operation not in {'revoke', 'upvote', 'downvote'}:
        raise wz_exceptions.BadRequest('Invalid operation')

    api = system_util.pillar_api()

    # PATCH the node and return the result.
    comment = Node({'_id': comment_id})
    result = comment.patch({'op': operation}, api=api)
    assert result['_status'] == 'OK'

    return jsonify({
        'status': 'success',
        'data': {
            'op': operation,
            'rating_positive': result.properties.rating_positive,
            'rating_negative': result.properties.rating_negative,
        }})
