import streamlit as st
from claim_processer import process_claims
import plotly.colors as colors

st.set_page_config(layout="wide")


def get_color_scale(score: float) -> str:
    """Convert score (1-10) to a hex color between red and green"""
    # Normalize score to 0-1 range
    normalized = (score - 1) / 9
    # Get color from red (0) to green (1)
    colors_scale = colors.n_colors('rgb(255,0,0)', 'rgb(0,255,0)', 12, colortype='rgb')
    color_index = int(normalized * 11)  # 11 because index starts at 0
    return colors_scale[color_index]

def main():
    st.image("./cover.png", width=300)
    st.title("TRUTH.io")
    
    # Create two columns for layout
    input_col, results_col = st.columns([1, 1])
    
    with input_col:
        # Text input
        user_text = st.text_area("Paste your text below to verify any claims within it.",
                                 height=300)
        verify_button = st.button("Verify Claims")

    with results_col:
        if verify_button:
            if user_text:
                with st.spinner("Analyzing claims..."):
                    results, _ = process_claims(user_text)

                    st.subheader("Verification Results")
                    for result in results:
                        # Updated condition to check for score 0 and empty sources
                        if not result['claim'].claim or (result['truthfullness_score'] == 0 and not result['sources']):
                            color = "#808080"  # Grey color
                        else:
                            color = get_color_scale(result['truthfullness_score'])
                        score = result['truthfullness_score']
                        
                        with st.container():
                            st.markdown(
                                f"""
                                <div style="padding: 20px; border-radius: 10px; background-color: {color}20; border-left: 5px solid {color};">
                                    <p style="color: {color};">Claim: {result['claim'].claim}</p>
                                    <div style="margin: 10px 0;">
                                        <div style="display: flex; align-items: center; gap: 10px;">
                                            <div style="flex-grow: 1; background-color: #eee; height: 10px; border-radius: 5px;">
                                                <div style="width: {score*10}%; background-color: {color}; height: 100%; border-radius: 5px;"></div>
                                            </div>
                                            <span>
                                                <strong>Truthfulness Score: {score}/10</strong>
                                            </span>
                                        </div>
                                    </div>
                                    <p><strong>Explanation:</strong> {result['explanation']}</p>
                                    <details>
                                        <summary>Sources</summary>
                                        <ul>
                                        {''.join([f'<li><a href="{source}">{source}</a></li>' for source in result['sources']])}
                                        </ul>
                                    </details>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                            st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.warning("Please enter some text to analyze.")

if __name__ == "__main__":
    main() 