import pandas as pd
from openai import OpenAI
import os
from datetime import datetime
import dotenv

dotenv.load_dotenv()

# Initialize the OpenAI client
client = OpenAI()

def analyze_reviews(csv_file: str, product_name: str) -> None:
    """
    Analyze G2 reviews using OpenAI's API to generate insights and save as markdown.
    
    Args:
        csv_file: Path to the CSV file containing G2 reviews
    """
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Split reviews into chunks of 20 reviews each
    chunk_size = 20
    review_chunks = [df['text'][i:i + chunk_size].tolist() for i in range(0, len(df), chunk_size)]
    # Limit to 5 chunks maximum
    review_chunks = review_chunks[:5]
    all_analyses = []
    
    for chunk_num, reviews_chunk in enumerate(review_chunks, 1):
        # Prepare the reviews text for this chunk
        reviews_text = "\n".join(reviews_chunk)
        
        # Create prompt for OpenAI - fixing the f-string formatting
        prompt = (
            f"Please analyze this batch of G2 reviews and provide insights in markdown format with:\n\n"
            "# Review Analysis Summary\n\n"
            "## 10 Positive Themes\n"
            "- Key positive themes and patterns\n"
            "  - provide up to 10 direct quotes from the reviews\n\n"
            "## 10 Negative Themes\n"
            "- Key negative themes and patterns\n"
            "  - provide up to 10 direct quotes from the reviews\n\n"
            "## Feature Requests & Pain Points\n"
            "- Most requested features\n"
            "  - provide up to 10 direct quotes from the reviews\n\n"
            "- Common pain points\n"
            "  - provide up to 10 direct quotes from the reviews\n\n"
            "## Overall Sentiment\n"
            "Summary of overall customer sentiment\n\n"
            f"Reviews analyzed:\n{reviews_text}"
        )
        
        try:
            print(f"Analyzing chunk {chunk_num} of {len(review_chunks)}...")
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing customer reviews and providing actionable insights. Format your response in markdown."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Get the analysis
            analysis = response.choices[0].message.content
            all_analyses.append(analysis)
            
        except Exception as e:
            print(f"Error during analysis of chunk {chunk_num}: {e}")
            continue
    
    # Combine all analyses
    final_prompt = (
        f"Please synthesize these {len(all_analyses)} review analysis chunks into a single cohesive analysis with the following format:"
            "# Review Analysis Summary\n\n"
            "## 10 Positive Themes\n"
            "- Key positive themes and patterns\n"
            "  - provide up to 10 direct quotes from the reviews\n\n"
            "## 10 Negative Themes\n"
            "- Key negative themes and patterns\n"
            "  - provide up to 10 direct quotes from the reviews\n\n"
            "## Feature Requests & Pain Points\n"
            "- Most requested features\n"
            "  - provide up to 10 direct quotes from the reviews\n\n"
            "- Common pain points\n"
            "  - provide up to 10 direct quotes from the reviews\n\n"
            "## Overall Sentiment\n"
            "Summary of overall customer sentiment\n\n"

            f"Review analysis chunks:\n{'---'.join(all_analyses)}"
            
    )
    
    try:
        # Generate final combined analysis
        final_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at synthesizing multiple review analyses into a single coherent summary. Format your response in markdown."},
                {"role": "user", "content": final_prompt}
            ]
        )
        
        final_analysis = final_response.choices[0].message.content
        
        # Save analysis to markdown file
        timestamp = datetime.now().strftime("%Y-%m-%d")
        output_file = f"analysis/review_analysis_{product_name}_{timestamp}.md"
        
        with open(output_file, "w") as f:
            f.write(f"# Analysis of {csv_file}\n")
            f.write("---\n\n")
            f.write(final_analysis)
            
        print(f"Analysis complete! Results saved to {output_file}")
        
    except Exception as e:
        print(f"Error during final analysis: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python analysis.py <path_to_csv> <product_name>")
        sys.exit(1)
    
        
    analyze_reviews(sys.argv[1], sys.argv[2])
