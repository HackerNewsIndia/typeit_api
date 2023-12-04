from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from dotenv import load_dotenv
import os
from bson import json_util
from bson import ObjectId

load_dotenv()
app = Flask(__name__)
CORS(app)
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
mongo = PyMongo(app)

# Define the MongoDB collection
typeit_space_collection = mongo.db.typeit_space


# @app.route('/create_typeit_space', methods=['POST'])
# def create_typeit_space():
#     data = request.get_json()
#     space_name = data.get('space_name')

#     # Insert the TypeIt space into the MongoDB collection
#     typeit_space_collection.insert_one({'space_name': space_name, 'comments': []})

#     return jsonify({'message': f'TypeIt Space "{space_name}" created successfully'})

@app.route('/api/create_typeit_space/<user_id>',methods=['POST'])
def create_typeitspace(user_id):
    data = request.get_json()
    space_name = data.get('name')
    space_id = ObjectId(data.get('_id'))
    typeit_space_collection.insert_one({'name': space_name, 'blog_id': space_id, 'user_id': ObjectId(user_id)})
    return jsonify({'message': f'TypeIt Space "{space_name}" created successfully'})



@app.route('/list_typeit_spaces/<user_id>', methods=['GET'])
def list_typeit_spaces(user_id):
    # Retrieve the list of TypeIt spaces from the MongoDB collection
    typeit_spaces = typeit_space_collection.find({"user_id": ObjectId(user_id)})
    
    # Convert the ObjectId to string for JSON serialization
    typeit_spaces_list = [{'_id': str(space['_id']), 'name': space['name']} for space in typeit_spaces]

    return jsonify({'typeit_spaces': typeit_spaces_list})



@app.route('/list_comments/<space_name>', methods=['GET'])
def list_comments(space_name):
    # Retrieve comments for a specific TypeIt space from the MongoDB collection
    typeit_space = typeit_space_collection.find_one({'space_name': space_name})

    if typeit_space:
        comments = typeit_space['comments']
        return jsonify({'comments': comments})
    else:
        return jsonify({'error': f'TypeIt Space "{space_name}" not found'}), 404


@app.route('/post_comment', methods=['POST'])
def post_comment():
    data = request.get_json()
    blogId = data.get('blog_id')
    postId = data.get('post_id')
    post_title = data.get('post_title')
    comment = data.get('comment')
    

    # Convert blogId and postId to ObjectId
    blog_id_object = ObjectId(blogId)
    post_id_object = ObjectId(postId)

    # Check if the post exists
    existing_post = typeit_space_collection.find_one({'blog_id': blog_id_object, 'posts_and_its_comments.post_id': post_id_object})

    if existing_post:
        # If the post exists, update its comments array
        result = typeit_space_collection.update_one(
            {'blog_id': blog_id_object, 'posts_and_its_comments.post_id': post_id_object},
            {'$push': {'posts_and_its_comments.$.comments': comment}}
        )
    else:
        # If the post doesn't exist, create a new post with comments
        result = typeit_space_collection.update_one(
            {'blog_id': blog_id_object},
            {
                '$push': {
                    'posts_and_its_comments': {
                        'post_id': post_id_object,
                        'post_title': post_title,  # Add post_title to the request JSON
                        'comments': [comment]
                    }
                }
            }
        )

    if result.modified_count > 0:
        return jsonify({'message': 'Comment added successfully'})
    else:
        return jsonify({'error': f'TypeIt Space or post not found'}), 404


@app.route('/get_comments/<post_id>', methods=['GET'])
def get_comments(post_id):
    try:
        # Find the TypeIt space using post_id
        typeit_space = typeit_space_collection.find_one({'posts_and_its_comments.post_id': ObjectId(post_id)})

        if typeit_space:
            # Extract comments for the specified post_id
            posts_and_comments = typeit_space.get('posts_and_its_comments', [])

            # Find the post with the specified post_id
            selected_post = next((post for post in posts_and_comments if post.get('post_id') == ObjectId(post_id)), None)

            if selected_post:
                comments = selected_post.get('comments', [])
                return jsonify({'comments': comments})
            else:
                return jsonify({'error': f'Post with ID "{post_id}" not found'}), 404
        else:
            return jsonify({'error': f'Post with ID "{post_id}" not found!'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
