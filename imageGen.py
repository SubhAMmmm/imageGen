import streamlit as st
import pandas as pd
import os
import time
import random
import traceback
from huggingface_hub import InferenceClient
import gc
 
def read_names_from_excel(uploaded_file):
    """Read names from uploaded Excel file."""
    try:
        df = pd.read_excel(uploaded_file)
        return df['Names'].tolist()
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return None
 
def generate_single_image(client, name, month, season_theme, output_dir, max_retries=3):
    """Enhanced image generation function with retry mechanism."""
    base_seed = {
        'January': 1000,
        'February': 2000,
        'March': 3000,
        'April': 4000,
        'May': 2000,
        'June': 6000,
        'July': 7000,
        'August': 8000,
        'September': 9000,
        'October': 10000,
        'November': 1000,
        'December': 12000
    }
   
    # Create name-specific output folder
    name_folder = os.path.join(output_dir, name)
    os.makedirs(name_folder, exist_ok=True)
   
    # Create prompt
    prompt = f"""Artistic Nature Photography: {season_theme}
 
            Landscape Composition:
            - Capture a breathtaking, immersive scene that embodies the {month} {season_theme}
            - Create a dynamic, high-detail landscape with vivid, natural colors
            - Integrate the name '{name}' organically into the scene
 
            Text Integration Guidelines:
            - The name '{name}' MUST be completely grounded within the natural environment
            - Text should not appear artificial or digitally overlaid
            - Text should be written in uppercase letters
            - Letters must emerge naturally from landscape elements
            - Text should be an artistic focal point that harmonizes with the scene
 
            Seasonal Text Transformation Techniques:
            - Winter Scene:
            * Letters carved in frost
            * Formed by snow patterns
            * Shaped by ice crystals
            * Emerging from snowy branches or frozen lake textures
 
            - Spring Scene:
            * Composed of blooming flowers
            * Created by fresh green shoots
            * Outlined by delicate plant stems
            * Integrated with new spring foliage
 
            - Summer Scene:
            * Sculpted by sunlight and shadows
            * Formed in beach sand or rocky terrain
            * Created by cloud formations
            * Emerging from natural landscape contours
 
            - Autumn Scene:
            * Constructed from falling leaves
            * Shaped by autumn tree bark
            * Outlined by forest floor textures
            * Integrated with harvest landscape elements
 
            - October Scene:
            * Letters formed by moss-covered stone textures
            * Created by delicate mushroom ring formations
 
            - November Scene:
            * Letters crafted through snow drift sculptural patterns
            * Formed by pine tree branch and needle arrangements
 
            Technical Specifications:
            - Ultra-high resolution
            - Hyper-realistic details
            - Natural lighting
            - Cinematic composition
            - Color palette true to the seasonal theme
            - Sharp focus on landscape and textual elements
            - Minimal post-processing
            - Authentic, unmanipulated appearance
 
            Photography Style:
            - Nature photography
            - Landscape cinematography
            - Organic, seamless integration
            - Artistic interpretation of natural scenery
 
            Mood and Atmosphere:
            - Capture the essence of {month}'s unique {season_theme}
            - Evoke emotional connection with the landscape
            - Create a sense of wonder and artistic discovery
 
            Avoid:
            - Digital text overlays
            - Artificial text placements
            - Forced or unnatural letter formations
            - Repeated text, merging text and missing text
            - Disconnected text elements or space between text"""
 
    for attempt in range(max_retries):
        try:
            # Generate image with exponential backoff
            image = client.text_to_image(
                prompt,
                seed=base_seed[month],
                height=960,
                width=1280
            )
 
            # Filename and path
            filename = f"{name}_{month}.png"
            filepath = os.path.join(name_folder, filename)
           
            # Save image
            image.save(filepath)
           
            # Longer rest between generations with increasing delay
            time.sleep(15 + (5 * attempt))
           
            return True, filepath
 
        except Exception as e:
            st.warning(f"Image generation attempt {attempt + 1} failed for {name} - {month}: {e}")
           
            # Exponential backoff before retrying
            time.sleep(2 ** attempt)
           
            # If it's the last attempt, log full traceback
            if attempt == max_retries - 1:
                st.error(f"Final attempt failed for {name} - {month}")
                st.error(traceback.format_exc())
                return False, None
 
    return False, None
 
def main():
    st.title("🖼️ Personalized Image Generator")
 
    # Sidebar Configuration
    st.sidebar.header("🔧 Generation Settings")
   
    # Inputs
    hf_token = st.sidebar.text_input("Hugging Face Token", type="password")
    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=['xlsx', 'xls'])
   
    output_dir = st.sidebar.text_input("Output Directory", value="generated_images")
   
    # Season Themes
    season_themes = {
    'January': 'Snowy Scandinavian forests, cozy cabin, grazing reindeer, aurora borealis glowing in serenity.',
    'February': 'Soft winter landscape, gentle snow-covered field, bare trees, pale blue sky, distant pink horizon at sunset.',
    'March': 'Cherry blossoms, Japanese garden, tranquil river, torii gate, Mount Fuji, floating pink petals.',
    'April': 'Dutch tulip fields, vibrant colors, windmill, canal reflection, cyclist, spring freshness, fluffy clouds.',
    'May': 'Spring, warm winds, bright flowers, blue skies',
    'June': 'Vibrant tropical beach scene, crystal-clear waters, swaying palm trees, golden sunset, colorful coral reefs.',
    'July': 'African savanna, golden hour, elephants, giraffes, lion, warm sunset, wildlife silhouettes, breezy grass.',
    'August': 'Mongolian grasslands, golden steppe, wild horses galloping, nomadic yurt, distant mountain silhouettes, thunderstorm brewing on horizon, amber light piercing storm clouds, windswept grass seas, eagle soaring, raw wilderness and untamed landscape.',
    'September': 'Fall harvest farm, golden fields, red barn, pumpkins, autumn foliage, sunset glow, tranquil landscape.',
    'October': 'New Zealand mystical Hobbiton, misty rolling green hills, ancient moss-covered stone walls, vintage wooden fences, soft morning fog, delicate mushroom clusters, rustic cottage with thatched roof, gentle stream, autumn-tinged maple trees, magical pastoral tranquility.',
    'November': 'Canadian Rocky Mountain wilderness, early winter alpine landscape, crystal-clear glacial lake, snow-dusted pine forests, lone timber wolf, rocky peaks emerging from cloud layers, soft lavender and steel-blue twilight, quiet anticipation of winter, wind-sculpted snow drifts, majestic wilderness solitude.',
    'December': 'German Christmas market, festive stalls, snow-covered houses, mulled wine, tree decorations, magical joyful ambiance.'
}
    months = list(season_themes.keys())
 
    # Generation Process
    if st.sidebar.button("🚀 Generate Images"):
        # Validate inputs
        if not hf_token:
            st.error("Please provide a Hugging Face Token")
            return
       
        if not uploaded_file:
            st.error("Please upload an Excel file")
            return
       
        # Prepare output directory
        os.makedirs(output_dir, exist_ok=True)
       
        # Read names
        names = read_names_from_excel(uploaded_file)
        if not names:
            return
       
        # Initialize client
        try:
            client = InferenceClient("black-forest-labs/FLUX.1-schnell", token=hf_token)
        except Exception as e:
            st.error(f"Client initialization error: {e}")
            return
       
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        image_gallery = st.container()
       
        # Generation results tracking
        generation_results = {}
       
        # Process each name
        for name_index, name in enumerate(names):
            status_text.info(f"Processing {name}")
           
            # Images for this name
            name_images = {}
           
            # Process all months for this name
            for month_index, month in enumerate(months):
                # Progress update
                progress = (name_index * len(months) + month_index + 1) / (len(names) * len(months))
                progress_bar.progress(progress)
               
                # Generate image
                season_theme = season_themes.get(month)
                success, filepath = generate_single_image(
                    client, name, month, season_theme, output_dir
                )
               
                # Track results and images
                name_images[month] = {
                    'success': success,
                    'filepath': filepath
                }
               
                # Display most recent image
                with image_gallery:
                    cols = st.columns(3)
                    with cols[1]:  # Center column
                        if success and filepath:
                            st.image(filepath, caption=f"{name} - {month}")
           
            # Store results
            generation_results[name] = name_images
           
            # Memory management
            gc.collect()
       
        # Finalization
        progress_bar.progress(1.0)
        status_text.success("Image Generation Complete!")
       
        # Detailed Results
        st.header("🔍 Generation Summary")
        for name, months_data in generation_results.items():
            with st.expander(f"{name} Image Generation"):
                for month, data in months_data.items():
                    status = "✅ Success" if data['success'] else "❌ Failed"
                    st.write(f"{month}: {status}")
 
if __name__ == "__main__":
    main()
has context menu
