import datetime
from datetime import timedelta
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import plotly.graph_objects as go
import time
import streamlit.components.v1 as components
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


# Function to get stock data
def get_stock_data(ticker, start, end):
    data = yf.download(ticker, start=start, end=end)
    return data

# Function to get sentiment analysis data
def get_sentiment_data(company_name, ticker, start, end):
    url = 'https://finance-news-api-wb4oco6h6a-ew.a.run.app/'
    params = {
        'company_name' : company_name,
        'company_ticker': ticker,
        'time_from': start.strftime('%Y%m%d'),
        'time_to': end.strftime('%Y%m%d'),
        'limit': 10
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error('Failed to fetch sentiment data.')
        return pd.DataFrame()

# Plotting function for stock data
def plot_stock_data(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Stock Price', mode='lines'))
    fig.update_layout(title='Stock Price', xaxis_title='Date', yaxis_title='Price')
    return fig


def plot_sentiment_data(data):
    # Ensure 'Time Published' is a datetime object for proper plotting
    if not pd.api.types.is_datetime64_any_dtype(data['Time Published']):
        try:
            data['Time Published'] = pd.to_datetime(data['Time Published'])
        except Exception as e:
            print(f"Error converting Time Published to datetime: {e}")
            return go.Figure()  # Return an empty figure on error

    fig = go.Figure()

    # Define colors for sentiments
    sentiment_colors = {
        'positive': 'green',  # Example green color
        'negative': 'red',    # Example red color
        'neutral': 'orange'   # Example neutral color
    }

    # Sort the data by 'Time Published' to have a chronological order on the x-axis
    data = data.sort_values('Time Published')

    # Plot a separate bar for each sentiment category
    for sentiment, color in sentiment_colors.items():
        subset = data[data['Model Sentiment'] == sentiment]
        if not subset.empty:
            fig.add_trace(go.Bar(
                x=subset['Time Published'],
                y=subset['Model Sentiment Score'],
                name=sentiment.capitalize(),
                marker_color=color
            ))

    # Update layout to adjust the look and feel of the plot
    fig.update_layout(
        title='Sentiment Analysis',
        xaxis=dict(
            title='Date and Time',
            tickformat='%Y-%m-%d %H:%M',  # Specify the desired tick format
            type='category'
        ),
        yaxis=dict(
            title='Score',
            fixedrange=True  # Disable zoom on y-axis
        ),
        barmode='group',
        legend_title='Sentiment',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        margin=dict(l=0, r=0, t=40, b=0),  # Reduce default margins
    )

    return fig

def format_time_published(data):
    # Format: '20230101T141404' -> '%Y%m%dT%H%M%S'
    data['Time Published'] = pd.to_datetime(data['Time Published'], format='%Y%m%dT%H%M%S')
    return data

def load_css(css_file):
    with open(css_file, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def color_sentiment(val):
    color = 'black'
    if val == 'positive':
        color = 'green'
    elif val == 'negative':
        color = 'red'
    elif val == 'neutral':
        color = 'skyblue'
    return f'color: {color};'

st.set_page_config(page_title="Stock Sentiment Analysis", layout="wide")

# Main function that orchestrates the app
def main():
    # Page configuration and title
    load_css("style.css")
    st.markdown("<h1 style='text-align: center; margin-bottom: -0.25em;'>Tech News Analysis</h1>", unsafe_allow_html=True)

    # Form for user input in the first column
    with st.sidebar:
        with st.form(key='sentiment_analysis_form'):
            company_name = st.text_input('Enter the company name')
            ticker_code = st.text_input('Enter ticker code').upper()
            start_date = st.date_input('Start date')
            end_date = st.date_input('End date')
            submit_button = st.form_submit_button(label='Analyze')
    col1, col2 = st.columns([1,1])
    sentiment_data = None

    # Check if inputs are filled
    if company_name and ticker_code and start_date and end_date:
        # Analyze button
        if submit_button:
            if end_date - start_date < timedelta(days=29):
                st.error("The gap between Start date and End date should be at least 30 days.")
                time.sleep(5)
                st.rerun()
            if start_date > datetime.date.today():
                st.error("Start date cannot be in the future.")
                time.sleep(5)
                st.rerun()
            if end_date > datetime.date.today():
                st.error("End date cannot be in the future.")
                time.sleep(5)
                st.rerun()
            if start_date == end_date:
                st.error("Start date and end date cannot be the same.")
                time.sleep(5)
                st.rerun()
            if start_date > end_date:
                st.error("End date must be after the start date.")
                time.sleep(5)
                st.rerun()
            try:
                with st.spinner('Fetching Data...'):
                    # Fetching the data
                    stock_data = get_stock_data(ticker_code, start_date, end_date)
                    sentiment_data = get_sentiment_data(company_name, ticker_code, start_date, end_date)
                    sentiment_data = format_time_published(sentiment_data)
                    if 'Preprocessed' in sentiment_data.columns:
                        sentiment_data = sentiment_data.drop(columns=['Preprocessed'])

                    # Plotting the stock data in the second column
                    with col1:
                        if not stock_data.empty:
                            stock_fig = plot_stock_data(stock_data)
                            st.plotly_chart(stock_fig, use_container_width=True)
                            st.markdown(f"<p style ='font-size: 24px;'>The plot above illustrates the stock price and sentiment analysis of {company_name} {ticker_code} for the specified time frame ({start_date}, {end_date}). The sentiment labels indicate whether the news associated with the company is perceived as positive, negative, or neutral. Upon comparing the plots, it's important to note that there isn't always a direct correlation between stock price movements and news sentiment. This observation stems from our analysis being based on a limited selection of recent news articles due to processing constraints.</p>",  unsafe_allow_html=True)
                    # Plotting the sentiment data in the third column
                    with col2:
                        if not sentiment_data.empty:
                            sentiment_fig = plot_sentiment_data(sentiment_data)
                            st.plotly_chart(sentiment_fig, use_container_width=True)
                    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
                    average_scores = sentiment_data.groupby('Model Sentiment')['Model Sentiment Score'].mean().to_dict()
                    with kpi_col1:
                        st.markdown(f"<div class='kpi-box'><h4>Average Positive Sentiment Score</h4><h3>{average_scores.get('positive', 0):.2f}</h3></div>", unsafe_allow_html=True)

                    with kpi_col2:
                        st.markdown(f"<div class='kpi-box'><h4>Average Neutral Sentiment Score</h4><h3>{average_scores.get('neutral', 0):.2f}</h3></div>", unsafe_allow_html=True)

                    with kpi_col3:
                        st.markdown(f"<div class='kpi-box'><h4>Average Negative Sentiment Score</h4><h3>{average_scores.get('negative', 0):.2f}</h3></div>", unsafe_allow_html=True)
                    st.subheader('Sentiment Data')
                    if not sentiment_data.empty:
                        sentiment_class_mapping = {
                            'positive': 'positive-sentiment',
                            'negative': 'negative-sentiment',
                            'neutral': 'neutral-sentiment'
                        }

                        # Apply classes to the 'Model Sentiment' column
                        sentiment_data['Model Sentiment'] = sentiment_data['Model Sentiment'].apply(
                            lambda x: f'<span class="{sentiment_class_mapping.get(x, "")}">{x}</span>'
                        )

                        # Convert the styled dataframe to HTML
                        df_html = sentiment_data.to_html(index=False, border=0, escape=False, formatters={
                            'Model Sentiment': lambda x: x
                        })

                        # Display the HTML within a styled container
                        st.markdown(f'<div class="dataframe-container">{df_html}</div>', unsafe_allow_html=True)
                    st.markdown("<p style='font-size: 24px;'>The above dataframe shows the most recent news headlines with summary. Hugging Face's algorithm assigns the sentiment label (positive, negative, neutral) along with a score.</p>", unsafe_allow_html=True)
            except Exception as e:
                st.error('An error occurred.')
                time.sleep(5)
                st.rerun()
    else:
        # If inputs are not filled, show a warning
        if submit_button:
            st.warning('Please fill in all input fields.')
            time.sleep(5)
            st.rerun()

# Run the main function
if __name__ == '__main__':
    main()
