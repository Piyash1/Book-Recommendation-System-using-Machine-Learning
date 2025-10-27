from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Load pickle files - try with pd.read_pickle first for compatibility
try:
    popular_df = pd.read_pickle('popular.pkl')
except:
    popular_df = pickle.load(open('popular.pkl','rb'))

try:
    pt = pd.read_pickle('pt.pkl')
except:
    pt = pickle.load(open('pt.pkl','rb'))

try:
    books = pd.read_pickle('books.pkl')
except:
    books = pickle.load(open('books.pkl','rb'))

similarity_scores = pickle.load(open('similarity_scores.pkl','rb'))

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html',
                           book_name=list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           image=list(popular_df['Image-URL-M'].values),
                           votes=list(popular_df['num_ratings'].values),
                           rating=list(popular_df['avg_rating'].values)
                           )

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

@app.route('/search_suggestions')
def search_suggestions():
    """Return book suggestions based on query"""
    query = request.args.get('q', '').lower()
    if len(query) < 2:
        return jsonify([])
    
    # Get matching books from pt (pivot table index)
    matching_books = [book for book in pt.index if query in book.lower()]
    return jsonify(matching_books[:10])  # Return top 10 suggestions

@app.route('/recommend_books', methods=['post'])
def recommend():
    user_input = request.form.get('user_input')
    
    # Error handling for empty input
    if not user_input or user_input.strip() == '':
        return render_template('recommend.html', data=None, error="Please enter a book name.")
    
    # Error handling for book not found
    if user_input not in pt.index:
        # Try case-insensitive match
        matching_books = [book for book in pt.index if book.lower() == user_input.lower()]
        if matching_books:
            user_input = matching_books[0]
        else:
            return render_template('recommend.html', 
                                 data=None, 
                                 error=f"Book '{user_input}' not found. Please try another book.")
    
    try:
        index = np.where(pt.index == user_input)[0][0]
        similar_items = sorted(list(enumerate(similarity_scores[index])), 
                             key=lambda x: x[1], reverse=True)[1:6]  # Get top 5 recommendations

        data = []
        for i in similar_items:
            item = {}
            temp_df = books[books['Book-Title'] == pt.index[i[0]]]
            if len(temp_df) > 0:
                unique_df = temp_df.drop_duplicates('Book-Title')
                item['title'] = unique_df['Book-Title'].values[0] if len(unique_df['Book-Title'].values) > 0 else ''
                item['author'] = unique_df['Book-Author'].values[0] if len(unique_df['Book-Author'].values) > 0 else ''
                item['image'] = unique_df['Image-URL-M'].values[0] if len(unique_df['Image-URL-M'].values) > 0 else ''
                item['similarity'] = round(i[1], 3)  # Store similarity score
                data.append(item)

        return render_template('recommend.html', data=data, searched_book=user_input)
    
    except IndexError:
        return render_template('recommend.html', 
                             data=None, 
                             error="An error occurred while processing your request.")
    except Exception as e:
        return render_template('recommend.html', 
                             data=None, 
                             error=f"Error: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)