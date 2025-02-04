from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint


SWAGGER_URL="/api/docs"  # (1) swagger endpoint e.g. HTTP://localhost:5002/api/docs
API_URL="/static/masterblog.json" # (2) ensure you create this dir and file

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Masterblog API' # (3) You can change this if you like
    }
)

app = Flask(__name__)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)
limiter = Limiter(app=app, key_func=get_remote_address)
CORS(app)  # This will enable CORS for all routes


POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
]


@app.route('/api/posts', methods=['GET', 'POST'])
@limiter.limit("10/minute")
def get_posts():
    if request.method == 'GET':
        return jsonify(POSTS)
    elif request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        if not data.get('title'):
            return jsonify({"error": "No title provided"}), 400
        if not data.get('content'):
            return jsonify({"error": "No content provided"}), 400

        post_title = data['title']
        post_content = data['content']
        highest_id = max((post['id'] for post in POSTS), default=0)
        POSTS.append({
            'id': highest_id + 1,
            'content': post_content,
            'title': post_title
        })
        return jsonify(POSTS)

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete(post_id):
    """Delete a blog post by ID."""
    global POSTS
    post_to_delete = next((post for post in POSTS if post['id'] == post_id), None)

    if post_to_delete is None:
        return jsonify({"error": "Post not found"}), 404

    POSTS = [post for post in POSTS if post['id'] != post_id]

    return jsonify({"message": "Post deleted successfully"}), 200

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update(post_id):
    global POSTS
    post_to_update = next((post for post in POSTS if post['id'] == post_id), None)
    if post_to_update is None:
        return jsonify({"error": "Post not found"}), 404
    data = request.get_json()
    if 'title' in data:
        post_to_update['title'] = data['title']
    if 'content' in data:
        post_to_update['content'] = data['content']

    return jsonify({
        "id": post_to_update['id'],
        "title": post_to_update['title'],
        "content": post_to_update['content']
    }), 200

@app.route('/api/posts/search', methods=['GET'])
def search_by_title():
    search_parameter = request.args.get('query', '').strip().lower()
    matching_posts = [post for post in POSTS if search_parameter in
                      post['title'].lower() or search_parameter in
                      post['content'].lower()]
    if matching_posts:
        return jsonify(matching_posts)
    else:
        return jsonify({"error": "Post not found "}), 404

@app.route('/api/posts', methods=['GET'])
def get_sorted_posts():
    sort_by = request.args.get('sort', '').strip().lower()
    direction = request.args.get('direction', 'asc').strip().lower()

    valid_sort_fields = {'title', 'content'}

    if sort_by in valid_sort_fields:
        reverse_order = direction == 'desc'
        sorted_posts = sorted(POSTS, key=lambda post: (post[sort_by] or "").lower(), reverse=reverse_order)
    else:
        sorted_posts = POSTS
    return jsonify(sorted_posts)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
