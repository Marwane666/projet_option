# Smart E-commerce Platform with User Persona Prediction

A modern e-commerce application that tracks user behavior and predicts user personas to optimize the shopping experience.

## Project Overview

This platform combines e-commerce functionality with advanced behavioral tracking and machine learning-based persona prediction. The system analyzes user navigation patterns, time spent on pages, interactions, and purchase behavior to categorize users into distinct personas, which can be used to personalize the shopping experience.

## Key Features

- **E-commerce Functionality**
  - Product browsing and catalog
  - Shopping cart management
  - Checkout process
  - Order confirmation
  
- **User Behavior Tracking**
  - Mouse movement tracking
  - Click and interaction recording
  - Scroll depth analysis
  - Session duration measurement
  
- **Persona Prediction**
  - AI-powered user persona classification (Découvreur, Précipité, Chercheur de bonnes affaires)
  - Recommendation generation based on personas
  - Real-time persona updates based on behavior
  
- **Analytics Dashboard**
  - Visual heatmaps of user activity
  - Session playback capabilities
  - User session metrics and statistics

## Technical Architecture

### Components

1. **Frontend**: HTML/CSS/JavaScript with session tracking
2. **Backend**: Flask web application
3. **Database**: MongoDB for storing user interactions and product data
4. **AI Module**: MistralAI-powered persona prediction system
5. **Vector Store**: For efficient storage and retrieval of text embeddings

### Data Flow

1. User visits the site and is assigned a unique user ID
2. User interactions are tracked and stored in MongoDB
3. Once sufficient data is collected, the persona prediction model is triggered
4. Based on the predicted persona, recommendations are generated
5. The application adjusts the UI/UX based on the persona

## Installation & Setup

### Prerequisites

- Python 3.8+
- MongoDB
- MistralAI API key

### Environment Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd projet_option
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your MistralAI API key:
   ```
   MISTRAL_API_KEY=your_api_key_here
   ```

5. Set up MongoDB:
   - Create a MongoDB Atlas account or use a local MongoDB server
   - Update the MongoDB connection string in `app.py`

### Running the Application

```
python app.py
```

The application will be available at `http://127.0.0.1:5000/`.

## Usage

### Shopping Experience

1. Browse the catalog at `/catalog`
2. View product details at `/product/<product_id>`
3. Add items to your cart
4. Proceed to checkout and complete your order

### Administration

1. Access the heatmap visualization at `/heatmap`
2. View session data for specific users and pages
3. Analyze user behavior patterns

## API Endpoints

### User Interaction Tracking

- `POST /record-session-data` - Record user session data including mouse movements, scrolling, and interactions
- `GET /get-user-sessions/<user>/<page>` - Get all sessions for a specific user and page
- `POST /get-movement-data` - Get aggregated movement data for analysis

### E-commerce Functionality

- `POST /add-to-cart` - Add an item to the shopping cart
- `POST /update-cart` - Update cart item quantity
- `POST /remove-from-cart` - Remove an item from the cart
- `POST /process-order` - Process a checkout order

### Persona Prediction

- `GET /predict-persona/<user_id>` - Trigger persona prediction for a specific user
- `GET /recommendations` - Get recommendations based on the user's predicted persona

## Technologies Used

- **Backend**: Flask, Python
- **Frontend**: HTML, CSS, JavaScript
- **Database**: MongoDB
- **Machine Learning**: MistralAI, llama_index
- **Vector Embeddings**: MistralAI Embedding
- **Data Visualization**: JavaScript (for heatmaps)

## Project Structure

```
projet_option/
│
├── V2/
│   ├── app.py                # Main Flask application
│   ├── predict_persona.py    # Persona prediction functionality
│   ├── templates/            # HTML templates
│   │   ├── acceuil.html
│   │   ├── catalog.html
│   │   ├── product.html
│   │   ├── cart.html
│   │   ├── checkout.html
│   │   ├── heatmap.html
│   │   └── ...
│   │
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   ├── data/
│   │   │   └── products.json  # Product catalog
│   │   └── videos/           # Tutorial videos
│   │
│   └── storage5/             # Vector store persistence directory
│
├── data_persona/             # Training data for persona models
│
└── personas/                 # Generated persona markdown files
```

## Persona Types

The system identifies three main user personas:

1. **Découvreur (Explorer)** - Users who like to browse and explore products thoroughly before making decisions
2. **Précipité (Hurried)** - Users who make quick decisions and want fast checkout experiences
3. **Chercheur de bonnes affaires (Bargain Hunter)** - Users who are primarily focused on finding deals and discounts

Each persona receives tailored recommendations:
- Explorers get step-by-step tutorials
- Hurried users get simplified checkout processes
- Bargain Hunters receive coupon and discount information

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
