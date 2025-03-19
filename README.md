# 💬 A/B Test Chatbot

A Streamlit app for A/B testing different language models using OpenRouter.

## How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Create a `.env` file with your OpenRouter API key:

   ```
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

3. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

## Deploying to Vercel

1. Push this repository to GitHub.

2. Connect your GitHub repository to Vercel.

3. Set the following environment variables in Vercel:
   - `OPENROUTER_API_KEY`: Your OpenRouter API key

4. Deploy! Vercel will automatically detect the configuration in `vercel.json`.

5. Note: You may need to adjust the output directory in your Vercel project settings.
