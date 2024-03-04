from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from dotenv import load_dotenv
import os
from bson import json_util
from bson import ObjectId
from datetime import datetime

load_dotenv()
app = Flask(__name__)
CORS(app)
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
mongo = PyMongo(app)

# Define the MongoDB collection
diaryblog_space_collection = mongo.db.diaryblog_space
diaryblog_post_collection = mongo.db.diaryblog_post
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
    timestamp = datetime.now()
    commented_user = data.get('commented_user')
    
    comment_id = ObjectId()

    # Convert blogId and postId to ObjectId
    blog_id_object = ObjectId(blogId)
    post_id_object = ObjectId(postId)

    # Check if the post exists
    existing_post = typeit_space_collection.find_one({'blog_id': blog_id_object, 'posts_and_its_comments.post_id': post_id_object})

    if existing_post:
        # If the post exists, update its comments array
        result = typeit_space_collection.update_one(
            {'blog_id': blog_id_object, 'posts_and_its_comments.post_id': post_id_object},
            {'$push': {
                        'posts_and_its_comments.$.comments': {
                            '_id': comment_id,
                            'comment': comment,
                            'timestamp': timestamp,
                            'commented_user': commented_user
                        }
                    }
            }
        )
        diaryblog_space_collection.update_one(
        {"_id": ObjectId(blog_id_object)},
        {"$inc": {"total_comments_count": 1}}
        )
        diaryblog_post_collection.update_one(
        {"_id": ObjectId(post_id_object)},
        {"$inc": {"total_comments_count": 1}}
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
                        'comments': [{
                            '_id': comment_id,
                            'comment': comment,
                            'timestamp': timestamp,
                            'commented_user': commented_user
                        }]
                    }
                }
            }
        )
        diaryblog_space_collection.update_one(
        {"_id": ObjectId(blog_id_object)},
        {"$inc": {"total_comments_count": 1}}
        )
        diaryblog_post_collection.update_one(
        {"_id": ObjectId(post_id_object)},
        {"$inc": {"total_comments_count": 1}}
        )
    if result.modified_count > 0:
        return jsonify({'message': 'Comment added successfully'})
    else:
        return jsonify({'error': f'TypeIt Space or post not found'}), 404


# @app.route('/get_comments/<post_id>', methods=['GET'])
# def get_comments(post_id):
#     try:
#         # Find the TypeIt space using post_id
#         typeit_space = typeit_space_collection.find_one({'posts_and_its_comments.post_id': ObjectId(post_id)})

#         if typeit_space:
#             # Extract comments for the specified post_id
#             posts_and_comments = typeit_space.get('posts_and_its_comments', [])

#             # Find the post with the specified post_id
#             selected_post = next((post for post in posts_and_comments if post.get('post_id') == ObjectId(post_id)), None)

#             if selected_post:
#                 comments = selected_post.get('comments', [])
#                 for comment in comments:
#                     comment['_id'] = str(comment['_id'])
                    
#                 return jsonify({'comments': comments})
#             else:
#                 return jsonify({'error': f'Post with ID "{post_id}" not found'}), 404
#         else:
#             return jsonify({'error': f'Post with ID "{post_id}" not found!'}), 404

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


@app.route('/get_comments/<post_id>', methods=['GET'])
def get_comments(post_id):
    try:
        # Assuming you have a MongoDB collection named 'posts' containing posts and comments
        # posts_collection = mongo.db.posts

        # Find the post by its ObjectId
        print(post_id)
        post = typeit_space_collection.find_one({"posts_and_its_comments.post_id": ObjectId(post_id)})

        if post:
            # post['_id'] = str(post['_id'])
            comments = post['posts_and_its_comments'][0].get('comments', [])
            print(comments)
            for comment in comments:
                    comment['_id'] = str(comment['_id'])
            print(comments)
            
            return jsonify({"comments": comments})
        else:
            return jsonify({"error": "Post not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route('/posts', methods=['GET'])
def get_posts():
    posts_from_db = list(typeit_space_collection.find({}, {'_id': 1, 'content': 1, 'likes': 1, 'loves': 1}))
    posts_with_counts = [
        {
            "_id": str(post["_id"]),
            "content": post["content"],
            "likes": post.get("likes", 0),
            "loves": post.get("loves", 0),
        }
        for post in posts_from_db
    ]
    return jsonify(posts_with_counts)

@app.route('/posts/<string:post_id>/like', methods=['POST'])
def like_post(post_id):
    post = typeit_space_collection.find_one({"_id": ObjectId(post_id)})
    if post:
        typeit_space_collection.update_one({"_id": ObjectId(post_id)}, {"$inc": {"likes": 1}})
        return jsonify({"message": "Post liked successfully"})
    else:
        return jsonify({"error": "Post not found"}), 404

@app.route('/posts/<string:post_id>/love', methods=['POST'])
def love_post(post_id):
    post = typeit_space_collection.find_one({"_id": ObjectId(post_id)})
    if post:
        typeit_space_collection.update_one({"_id": ObjectId(post_id)}, {"$inc": {"loves": 1}})
        return jsonify({"message": "Post loved successfully"})
    else:
        return jsonify({"error": "Post not found"}), 404
    

@app.route('/post_sentiment', methods=['POST'])
def post_sentiment():
    try:
        data = request.get_json()

        blog_id = data.get('blog_id')
        post_id = data.get('post_id')
        comment_id = data.get('comment_id')
        sentiment_type = data.get('sentiment_type')
        user_who_selected_this_icon = data.get('user_who_selected_this_icon')
        print(sentiment_type)
        print(user_who_selected_this_icon)

        existing_comment = typeit_space_collection.find_one({
            'blog_id': ObjectId(blog_id),
            'posts_and_its_comments.post_id': ObjectId(post_id),
            'posts_and_its_comments.comments._id': ObjectId(comment_id)
        })

        if existing_comment:
            # If the comment exists, update its sentiments array
            typeit_space_collection.update_one(
                {
                    'blog_id': ObjectId(blog_id),
                    'posts_and_its_comments.post_id': ObjectId(post_id),
                    'posts_and_its_comments.comments._id': ObjectId(comment_id)
                },
                {
                    '$set': {
                                f'posts_and_its_comments.$[post].comments.$[comm].sentiments.{sentiment_type}': [user_who_selected_this_icon]
                            }
                            
                },
                array_filters=[
                    {'post.comments._id': ObjectId(comment_id)},
                    {'comm._id': ObjectId(comment_id)}
                ]
            )
            return jsonify({'message': 'Sentiment added successfully'})
        else:
            # If the comment doesn't exist, return an error
            return jsonify({'error': f'Comment_id not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_sentiment', methods=['GET'])
def get_sentiment():
    try:
        # Assuming you want to retrieve sentiments based on blog_id, post_id, and comment_id
        blog_id = request.args.get('blog_id')
        post_id = request.args.get('post_id')
        comment_id = request.args.get('comment_id')

        existing_comment = typeit_space_collection.find_one({
            'blog_id': ObjectId(blog_id),
            'posts_and_its_comments.post_id': ObjectId(post_id),
            'posts_and_its_comments.comments._id': ObjectId(comment_id)
        })

        if existing_comment:
            # If the comment exists, retrieve sentiments
            sentiments = existing_comment['posts_and_its_comments'][0]['comments'][0]['sentiments']
            return jsonify({'sentiments': sentiments})
        else:
            # If the comment doesn't exist, return an error
            return jsonify({'error': 'Comment not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/blog_comments_count/<string:blog_id>', methods=['GET'])
def get_blog_comments_count(blog_id):
    # Convert blog_id to ObjectId
    blog_id_object = ObjectId(blog_id)
    
    # Query the MongoDB collection for posts under the specified blog_id
    posts = typeit_space_collection.find({'blog_id': blog_id_object})

    total_comments_count = 0
    
    # Iterate through each post and calculate the total number of comments
    for post in posts:
        if 'posts_and_its_comments' in post:
            for post_comments in post['posts_and_its_comments']:
                if 'comments' in post_comments:
                    total_comments_count += len(post_comments['comments'])

    return jsonify({'total_comments_count': total_comments_count})



if __name__ == '__main__':
    app.run(debug=True)
