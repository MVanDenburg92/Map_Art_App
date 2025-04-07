from streamlit_folium import st_folium
import streamlit as st
import osmnx as ox
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import folium
from folium import Map
import io
from folium import Marker
import numpy as np
import time

# Set page to wide mode by default
st.set_page_config(layout="wide")

@st.cache_data
def get_graph(place=None, bbox=None):
    """Get graph either from a place name or a bounding box"""
    if place:
        try:
            return ox.graph.graph_from_place(place, network_type="all")
        except Exception as e:
            st.error(f"Error fetching place: {e}")
            return None
    elif bbox:
        left, bottom, right, top = bbox[3], bbox[1], bbox[2], bbox[0]
        return ox.graph.graph_from_bbox((left, bottom, right, top), network_type="all")
    return None

def get_place_coordinates(place, focus_downtown=True):
    """Get coordinates for a place name, focusing on downtown if requested"""
    try:
        # If focus_downtown is True, add 'downtown' to the search query
        search_query = f"downtown {place}" if focus_downtown else place
        
        # Get the geocoded place
        gdf = ox.geocode_to_gdf(search_query)
        
        if gdf.empty:
            # If downtown search fails, try without downtown
            if focus_downtown:
                st.warning(f"Could not find downtown for '{place}'. Trying general location instead.")
                return get_place_coordinates(place, focus_downtown=False)
            return None
            
        # Get the centroid of the geometry
        centroid = gdf.geometry.iloc[0].centroid
        return centroid.y, centroid.x
    except Exception as e:
        if focus_downtown:
            st.warning(f"Error finding downtown for '{place}'. Trying general location instead.")
            return get_place_coordinates(place, focus_downtown=False)
        st.error(f"Error geocoding location: {e}")
        return None

def extract_graph_edges(G):
    u, v, key, data = zip(*G.edges(keys=True, data=True))
    return list(u), list(v), list(key), list(data)

def classify_road_segments(data, custom_colors, custom_widths):
    road_colors = []
    road_widths = []

    for item in data:
        if "length" in item:
            if item["length"] <= 100:
                linewidth, color = custom_widths["<100"], custom_colors["<100"]
            elif item["length"] <= 200:
                linewidth, color = custom_widths["100-200"], custom_colors["100-200"]
            elif item["length"] <= 400:
                linewidth, color = custom_widths["200-400"], custom_colors["200-400"]
            elif item["length"] <= 800:
                linewidth, color = custom_widths["400-800"], custom_colors["400-800"]
            else:
                linewidth, color = custom_widths[">800"], custom_colors[">800"]

            if "primary" in item.get("highway", ""):
                linewidth, color = custom_widths["primary"], custom_colors["primary"]
        else:
            linewidth, color = custom_widths[">800"], custom_colors[">800"]

        road_colors.append(color)
        road_widths.append(linewidth)

    return road_colors, road_widths

def plot_graph(G, road_colors, road_widths, background_color):
    fig, ax = ox.plot_graph(G, node_size=0, dpi=300, bgcolor=background_color,
                            edge_color=road_colors, edge_linewidth=road_widths, edge_alpha=1, show=False)
    return fig, ax

def add_legend(ax, custom_colors, markersize=16, fontsize=16):
    legend_elements = [
        Line2D([0], [0], marker='s', color="#061529", label='Length < 100 m',
               markerfacecolor=custom_colors["<100"], markersize=markersize),
        Line2D([0], [0], marker='s', color="#061529", label='100-200 m',
               markerfacecolor=custom_colors["100-200"], markersize=markersize),
        Line2D([0], [0], marker='s', color="#061529", label='200-400 m',
               markerfacecolor=custom_colors["200-400"], markersize=markersize),
        Line2D([0], [0], marker='s', color="#061529", label='400-800 m',
               markerfacecolor=custom_colors["400-800"], markersize=markersize),
        Line2D([0], [0], marker='s', color="#061529", label='> 800 m',
               markerfacecolor=custom_colors[">800"], markersize=markersize),
        Line2D([0], [0], marker='s', color="#061529", label='Primary',
               markerfacecolor=custom_colors["primary"], markersize=markersize),
    ]

    legend = ax.legend(handles=legend_elements, bbox_to_anchor=(0.0, 0.0), frameon=True, ncol=1,
                       facecolor='#061529', framealpha=0.9, loc='lower left', fontsize=fontsize,
                       prop={'family': "Georgia", 'size': fontsize})

    for text in legend.get_texts():
        text.set_color("w")

def apply_style_preset(preset):
    presets = {
        "Minimal": {
            "colors": {"<100": "#cccccc", "100-200": "#bbbbbb", "200-400": "#999999",
                       "400-800": "#777777", ">800": "#555555", "primary": "#000000"},
            "background": "#ffffff"
        },
        "Bold": {
            "colors": {"<100": "#d40a47", "100-200": "#e78119", "200-400": "#30bab0",
                       "400-800": "#bbbbbb", ">800": "#ffffff", "primary": "#ffffff"},
            "background": "#31bab0"
        },
        "Midnight": {
            "colors": {"<100": "#5dd39e", "100-200": "#348aa7", "200-400": "#525174",
                       "400-800": "#513b56", ">800": "#6c8ead", "primary": "#ffffff"},
            "background": "#061529"
        }
    }
    return presets.get(preset)

def main():
    # Safe session key initialization with added stored_lat and stored_lon
    for key, default in {
        "marker_pos": {"lat": 42.3579, "lng": -71.0604},
        "map_center": [42.3579, -71.0604],
        "map_zoom": 14,
        "last_input_method": None,
        "stored_lat": 42.3579,  # Added separate storage for lat
        "stored_lon": -71.0604,  # Added separate storage for lon
        "location_set": False,   # Flag to track if location was set from place name
        "location_name": ""      # Store the currently selected location name
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default
            
    st.title("🗘️ OSM Street Map Visualizer")

    ox.settings.requests_kwargs = {'verify': False}

    # Create two columns for the sidebar and main content
    sidebar, main_content = st.columns([1, 3])
    with sidebar:
        # Input options
        st.markdown("### Select Location")

        input_method = st.radio("Choose your location input method:", ["Location Name", "Coordinates"])
        
        # Store the previous input method to detect changes
        input_method_changed = st.session_state.get("last_input_method") != input_method
        st.session_state["last_input_method"] = input_method
        
        use_place = input_method == "Location Name"
        
        if use_place:
            # Get current place name or default
            default_place = st.session_state.get("location_name", "Boston, MA")
            place = st.text_input("Enter a location:", default_place)
            focus_downtown = st.checkbox("Focus on downtown area", value=True)
            
            # Track if the place name has changed
            place_changed = place != st.session_state.get("location_name", "")
            st.session_state["location_name"] = place
            
            # Only update map position if the place name has changed or the location has never been set
            if place and (place_changed or not st.session_state["location_set"]):
                # Try to get coordinates from place name
                coords = get_place_coordinates(place, focus_downtown=focus_downtown)
                if coords:
                    center_lat, center_lon = coords
                    st.session_state["map_center"] = [center_lat, center_lon]
                    st.session_state["marker_pos"] = {"lat": center_lat, "lng": center_lon}
                    st.session_state["stored_lat"] = center_lat  # Update stored values too
                    st.session_state["stored_lon"] = center_lon  # Update stored values too
                    
                    # Set a closer zoom level for downtown areas if this is the first time setting location
                    if focus_downtown and not st.session_state["location_set"]:
                        st.session_state["map_zoom"] = 16
                    
                    # Mark that we've set the location
                    st.session_state["location_set"] = True
                else:
                    st.warning(f"Could not find coordinates for '{place}'. Using default coordinates.")
                    center_lat = st.session_state["map_center"][0]
                    center_lon = st.session_state["map_center"][1]
            else:
                # Use existing coordinates
                center_lat = st.session_state["marker_pos"]["lat"]
                center_lon = st.session_state["marker_pos"]["lng"]
                
        else:
            place = None
            # Initialize coordinate inputs with stored values instead of directly accessing map_center
            center_lat = st.number_input("Center Latitude", value=st.session_state["stored_lat"], format="%f", key="coord_lat")
            center_lon = st.number_input("Center Longitude", value=st.session_state["stored_lon"], format="%f", key="coord_lon")
            
            # When not using place names, apply the current marker position directly to the input fields
            # FIXED: Apply button now just uses these input values directly instead of trying to read them again
            
        # bbox_size = st.slider("Bounding Box Size", 0.005, 0.05, 0.015, step=0.005)
        
        # Apply button for coordinate mode to explicitly update the map
        if not use_place:
            col1_, col2_, col3_, col_4 = st.columns([9,8,8,8])
            with col1_:
                # st.button("👍")
                if st.button("Apply Input Coordinates", key="apply_coords"):
                    # Use the current input field values
                    lat = st.session_state["coord_lat"]
                    lng = st.session_state["coord_lon"]
                    
                    # Update stored values
                    st.session_state["stored_lat"] = lat
                    st.session_state["stored_lon"] = lng
                    
                    # Update marker position and map center
                    st.session_state["marker_pos"] = {"lat": lat, "lng": lng}
                    st.session_state["map_center"] = [lat, lng]
                    
                    st.success(f"Coordinates updated to: ({lat:.5f}, {lng:.5f})")
                    st.rerun()
                if not (-90 <= center_lat <= 90) or not (-180 <= center_lon <= 180):
                    st.error("Please enter valid latitude and longitude.")
                    return

            # Button to get current marker position
            with col2_:
                # st.button("👎")
                if st.button("Move the Marker", key="get_pos"):
                    # This button updates the input fields with the current marker position
                    lat = st.session_state["marker_pos"]["lat"]
                    lng = st.session_state["marker_pos"]["lng"]
                    
                    st.session_state["stored_lat"] = lat
                    st.session_state["stored_lon"] = lng
                    
                    # Update the coordinate input fields
                    st.success(f"Input fields updated with marker position: ({lat:.5f}, {lng:.5f})")
                    st.rerun()
            with col3_:
                # Button to center map on marker
                if st.button("Center Map on Marker", key="center_map"):
                    # This button centers the map view on the current marker position
                    lat = st.session_state["marker_pos"]["lat"]
                    lng = st.session_state["marker_pos"]["lng"]
                    
                    # Update map center to match marker position
                    st.session_state["map_center"] = [lat, lng]
                    
                    st.success(f"Map centered on marker position: ({lat:.5f}, {lng:.5f})")
                    st.rerun()
        # Reset button
            with col_4:
                if st.button("Reset Map to Boston", key="reset_button"):
                    st.session_state["marker_pos"] = {"lat": 42.3579, "lng": -71.0604}
                    st.session_state["map_center"] = [42.3579, -71.0604]
                    st.session_state["map_zoom"] = 14
                    st.session_state["stored_lat"] = 42.3579  # Reset stored values too
                    st.session_state["stored_lon"] = -71.0604  # Reset stored values too
                    st.session_state["location_set"] = False  # Reset location flag
                    st.session_state["location_name"] = ""    # Reset location name
                    st.rerun()
        bbox_size = st.slider("Bounding Box Size", 0.005, 0.05, 0.015, step=0.005)
        st.markdown("### Style Options")
        preset = st.selectbox("Apply a style preset?", ["None", "Minimal", "Bold", "Midnight"])

        transparent_bg = st.checkbox("Transparent Background", value=False)
        if transparent_bg:
            background_color = "none"
        else:
            background_color = st.color_picker("Background Color", value="#31bab0")

        show_legend = st.checkbox("Show Legend", value=True)
        
        # Road style settings directly in sidebar (no nested columns)
        with st.expander("Road Style Settings", expanded=False):
            # Custom style overrides
            st.markdown("#### Road Colors & Widths")
            default_colors = {
                "<100": "#d40a47", "100-200": "#e78119", "200-400": "#30bab0",
                "400-800": "#bbbbbb", ">800": "#ffffff", "primary": "#ffffff"
            }
            default_widths = {
                "<100": 0.3, "100-200": 0.45, "200-400": 0.6,
                "400-800": 0.75, ">800": 0.5, "primary": 0.8
            }

            custom_colors = {}
            custom_widths = {}

            for key in default_colors.keys():
                st.write(f"**{key}**")
                custom_colors[key] = st.color_picker(f"Color {key}", value=default_colors[key], key=f"color_{key}")
                custom_widths[key] = st.slider(f"Width {key}", 0.1, 2.0, default_widths[key], step=0.05, key=f"width_{key}")
                st.divider()
        
        # Generate button
        generate_map = st.button("Generate Map", use_container_width=True)
            
    with main_content:
        # Create columns for map and info - no nesting here
        map_col, info_col = st.columns([10, .1])
        
        with map_col:
            st.markdown("### Interactive Map Selection")
            # Display marker location below the map
            marker_pos = st.session_state["marker_pos"]
            map_center = st.session_state["map_center"]
            map_zoom = st.session_state["map_zoom"]

            # Create the folium map
            m = folium.Map(location=map_center, zoom_start=map_zoom)
            folium.plugins.Fullscreen(
                position="topright",
                title="Expand me",
                title_cancel="Exit me",
                force_separate_button=True,
            ).add_to(m)
            # folium.plugins.LocateControl().add_to(m)

            # If you want get the user device position after load the map, set auto_start=True
            folium.plugins.LocateControl(auto_start=False).add_to(m)

            # Add draggable marker
            marker = folium.Marker(
                location=[marker_pos["lat"], marker_pos["lng"]],
                draggable=False,
                tooltip="Click the map to move me"
            ).add_to(m)

            # Display map with a specific key for proper state tracking
            map_data = st_folium(m, height=780, width=None, key="folium_map")
    
            # st.markdown("### Current Location")
            # st.write(f"Latitude: {marker_pos['lat']:.5f}")
            # st.write(f"Longitude: {marker_pos['lng']:.5f}")
            
            # Add buttons to interact with the marker
            # if not use_place:
            #     # Button to get current marker position
            #     if st.button("Move the Marker", key="get_pos"):
            #         # This button updates the input fields with the current marker position
            #         lat = st.session_state["marker_pos"]["lat"]
            #         lng = st.session_state["marker_pos"]["lng"]
                    
            #         st.session_state["stored_lat"] = lat
            #         st.session_state["stored_lon"] = lng
                    
            #         # Update the coordinate input fields
            #         st.success(f"Input fields updated with marker position: ({lat:.5f}, {lng:.5f})")
            #         st.rerun()
                
            #     # Button to center map on marker
            #     if st.button("Center Map on Marker", key="center_map"):
            #         # This button centers the map view on the current marker position
            #         lat = st.session_state["marker_pos"]["lat"]
            #         lng = st.session_state["marker_pos"]["lng"]
                    
            #         # Update map center to match marker position
            #         st.session_state["map_center"] = [lat, lng]
                    
            #         st.success(f"Map centered on marker position: ({lat:.5f}, {lng:.5f})")
            #         st.rerun()
            # Debug output
            if st.checkbox("Show Debug Info", value=False):
                st.write("Map Data:", map_data)
        # Handles map clicks and drags
        def floats_close(a, b, tol=1e-2):
            return abs(a - b) < tol

        # Update marker position if clicked or dragged
        if map_data:
            # Track last clicked position on map
            if map_data.get("last_clicked"):
                lat, lng = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
                # Update marker position
                st.session_state["marker_pos"] = {"lat": lat, "lng": lng}
                # Add info about marker position
                if not use_place:
                    st.info(f"Map clicked at: ({lat:.5f}, {lng:.5f})")
            
            # Also update map center based on panning
            if map_data.get("center"):
                lat, lon = map_data["center"]["lat"], map_data["center"]["lng"]
                prev_lat, prev_lon = st.session_state["map_center"]
                if not (floats_close(lat, prev_lat) and floats_close(lon, prev_lon)):
                    st.session_state["map_center"] = [lat, lon]

            # Track zoom changes
            if map_data.get("zoom") and not floats_close(map_data["zoom"], st.session_state["map_zoom"]):
                st.session_state["map_zoom"] = map_data["zoom"]

        # Apply preset override if selected
        if preset != "None":
            style = apply_style_preset(preset)
            custom_colors = style["colors"]
            if not transparent_bg:
                background_color = style["background"]

        # Only generate the map when the button is clicked
        if "generate_map" in locals() and generate_map:
            with st.spinner("Generating..."):
                # Get the bounding box centered on current marker position, not map center
                # This ensures the generated map shows the area around the marker
                center_lat = st.session_state["marker_pos"]["lat"]
                center_lon = st.session_state["marker_pos"]["lng"]
                
                # Get the appropriate search query based on downtown focus
                if use_place and place:
                    search_query = place
                    if "focus_downtown" in locals() and focus_downtown:
                        # When getting the actual graph, we'll use a smaller area
                        # but continue to use the original place name
                        bbox_size = min(bbox_size, 0.015)  # Smaller bounding box for downtown
                    
                    # Use place name to get graph
                    G = get_graph(place=search_query)
                else:
                    # Use bounding box to get graph
                    bbox = (center_lat + bbox_size, center_lat - bbox_size, center_lon + bbox_size, center_lon - bbox_size)
                    G = get_graph(bbox=bbox)

                if not G or not G.edges:
                    st.error("No road data found. Try adjusting your input.")
                else:
                    _, _, _, data = extract_graph_edges(G)
                    road_colors, road_widths = classify_road_segments(data, custom_colors, custom_widths)
                    fig, ax = plot_graph(G, road_colors, road_widths, background_color)

                    if show_legend:
                        add_legend(ax, custom_colors)

                    st.session_state.fig = fig  # 💾 Save the figure to session state

        # ✅ Display the plot and download options if a map has been generated
        if "fig" in st.session_state:
            # Use full width for the visualization
            st.pyplot(st.session_state.fig, use_container_width=True)

            # Export options - without nesting columns
            download_cols = st.columns([3, 1])
            with download_cols[0]:
                # Let user name the file
                filename = st.text_input("Filename for download (no extension)", value="street_map")
            
            with download_cols[1]:
                # Image export
                buf = io.BytesIO()
                st.session_state.fig.savefig(
                    buf, format="png", dpi=300, bbox_inches='tight',
                    transparent=(background_color == "none")
                )

                st.download_button(
                    "Download Map as PNG",
                    data=buf.getvalue(),
                    file_name=f"{filename}.png",
                    mime="image/png",
                    use_container_width=True
                )


if __name__ == "__main__":
    main()