<img src='Map_Art_App\images\street_map_adjusted_Boston.png'>

# Map Art App

A Streamlit application that generates artistic map visualizations using OpenStreetMap data.

## 📝 Description

Map Art App uses the power of OSMnx and Folium to create beautiful map visualizations from any location around the world. Simply enter a location, customize the styling, and download your personalized map art.

## ✨ Features

- Interactive map selection using Folium
- Customizable map styles and colors
- Export maps as high-resolution images
- Various map visualization types (streets, buildings, etc.)
- Responsive design for desktop and mobile use

## 🚀 Installation

### Prerequisites

- Python 3.13 or higher

### Set up

1. Clone this repository:
```bash
git clone https://github.com/yourusername/map_art_app.git
cd map_art_app
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install the package in development mode:
```bash
pip install -e .
```

## 🏃‍♀️ Running the App

The app is contained in a single file for simplicity. To run:

```bash
streamlit run map_art_app.py
```

The app will open in your default web browser at `http://localhost:8501`.

## 📦 Dependencies

- `streamlit`: Web application framework
- `folium`: Interactive map visualizations
- `streamlit-folium`: Integration between Streamlit and Folium
- `osmnx`: Retrieving, modeling, analyzing, and visualizing OpenStreetMap data
- `matplotlib`: Visualization library for map rendering
- `numpy`: Numerical computations

## 🔧 Usage

1. Enter a location in the search bar (city, address, or coordinates)
2. Customize your map's appearance using the sidebar controls:
   - Map type (streets, buildings, etc.)
   - Color scheme
   - Border and background settings
3. Click "Generate Map Art" to create your visualization
4. Download the image by clicking the "Download" button

## 📋 Project Structure

```
map_art_app/
├── map_art_app.py    # Main Streamlit application
├── setup.py          # Package installation configuration
├── pyproject.toml    # Modern Python project configuration
├── requirements.txt  # Dependencies for deployment
├── README.md         # This documentation
└── .gitignore        # Files to exclude from version control
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Contact

If you have any questions or feedback, please open an issue on GitHub.  Thanks and happy mapping!