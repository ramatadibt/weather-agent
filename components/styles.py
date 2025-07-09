def load_css():
  '''
  Returns the CSS style for the application 
  ''' 
  return """
        <style>
            .main {
                background-color: #1a2942;  /* Darker blue background */
                color: #E0E0E0;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 10px;
                justify-content: center;
                width: 100%;
                background-color: #233656;  /* Slightly lighter blue */
                padding: 10px 0;
            }
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                white-space: pre-wrap;
                border-radius: 4px 4px 0px 0px;
                gap: 1px;
                padding: 10px 20px;
                background-color: #233656;  /* Matching blue */
                color: #E0E0E0;
                min-width: 120px;
                text-align: center;
                flex-grow: 1;
            }
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background-color: #ff8c42;  /* Warm orange for active tab */
                color: #FFFFFF;
            }
            div[data-testid="stVerticalBlock"] > div:has(div.element-container) {
                background-color: #1a2942;  /* Matching main background */
                padding: 0.5rem;
                border-radius: 10px;
            }
            div.stMetric {
                background-color: #233656;  /* Consistent blue */
                padding: 15px;
                border-radius: 8px;
                color: #E0E0E0;
            }
            div.chat-message {
                padding: 1.5rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
                display: flex;
            }
            div.chat-message.user {
                background-color: #2d4b73;  /* Lighter blue for user messages */
                color: #E0E0E0;
            }
            div.chat-message.bot {
                background-color: #233656;  /* Consistent blue for bot messages */
                color: #E0E0E0;
            }
            div.chat-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                object-fit: cover;
                margin-right: 1rem;
            }
            div.chat-content {
                flex-grow: 1;
                color: #E0E0E0;
            }
            div.chat-container {
                height: 400px;
                overflow-y: auto;
                padding: 1rem;
                border-radius: 0.5rem;
                background-color: #1a2942;
                color: #E0E0E0;
            }
            .avatar-img {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                object-fit: cover;
            }
            div.weather-card {
                background-color: #233656;
                border-radius: 10px;
                padding: 20px;
                color: #E0E0E0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .daily-forecast-card {
                background-color: #2d4b73;  /* Lighter blue for cards */
                border-radius: 8px;
                padding: 10px;
                text-align: center;
                transition: transform 0.2s;
                color: #E0E0E0;
                border: 1px solid rgba(255, 140, 66, 0.1);  /* Subtle orange border */
            }
            .daily-forecast-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(255, 140, 66, 0.2);  /* Orange glow on hover */
            }
            .hourly-forecast-card {
                background-color: #2d4b73;
                border-radius: 8px;
                padding: 10px;
                text-align: center;
                transition: transform 0.2s;
                color: #E0E0E0;
                border: 1px solid rgba(255, 140, 66, 0.1);
            }
            .hourly-forecast-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(255, 140, 66, 0.2);
            }
            .pollutant-card {
                background-color: #34495E;
                padding: 10px;
                border-radius: 10px;
                text-align: center;
                color: #E0E0E0;
                margin: 5px;
            }
            .metric-value {
                font-size: 24px;
                font-weight: bold;
                color: #FFFFFF;
            }
            .metric-label {
                font-size: 14px;
                color: #D3D3D3;
            }
            .pollutant-value {
                font-size: 22px;
                font-weight: bold;
                color: #FFFFFF;
            }
            .forecast-value {
                font-size: 20px;
                font-weight: bold;
                color: #FFFFFF;
            }
            .forecast-label {
                font-size: 14px;
                color: #D3D3D3;
            }
            .section-title {
                font-size: 20px;
                font-weight: 500;
                margin-bottom: 15px;
                color: #F5F6FA;
            }
            .location-title {
                font-size: 24px;
                font-weight: bold;
                color: #E0E0E0;
                margin-bottom: 10px;
            }
            input.st-text-input > div > input {
                color: #E0E0E0;  /* Ensure text is visible */
                background-color: #233656;
                height: 2rem;  /* Consistent height */
                padding: 0.25rem 0.5rem;  /* Reduced padding for compactness */
                vertical-align: middle;  /* Align with button */
                line-height: normal;  /* Reset line-height to prevent vertical text */
                white-space: nowrap;  /* Prevent text wrapping */
                width: 100%;  /* Ensure input takes full available width */
                font-size: 14px;  /* Reduce font size if needed */
                border: 1px solid rgba(255, 140, 66, 0.2);
            }
            input.st-text-input > div > input::placeholder {
                color: #D3D3D3;  /* Improved contrast for placeholder */
                opacity: 1;     /* Ensure placeholder is fully visible */
                font-size: 14px;  /* Match input font size */
            }
            .stButton > button {
        height: auto;  /* Allow height to adjust based on content */
        min-height: 3rem;  /* Ensure a minimum height for consistency */
        padding: 0.5rem 1rem;  /* Adjust padding for better fit */
        font-size: 12px;  /* Reduce font size to fit text */
        line-height: 1.2;  /* Adjust line height for better text alignment */
        white-space: normal;  /* Allow text to wrap naturally */
        word-wrap: break-word;  /* Ensure long words break to fit */
        display: flex;  /* Use flexbox to center content */
        align-items: center;  /* Center vertically */
        justify-content: center;  /* Center horizontally */
        text-align: center;  /* Ensure text is centered */
        background-color: #ff8c42 !important;
        color: #FFFFFF !important;
        border: none !important;
        transition: all 0.3s ease !important;
        }
                    .main-weather-card {
            display: flex;
            flex-direction: column;
            background-color: #233656;  /* Consistent blue */
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid rgba(255, 140, 66, 0.15);  /* Subtle orange border */
        }
        
        .weather-primary {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        
        .temperature-large {
            font-size: 48px;
            font-weight: bold;
            color: #ff8c42;  /* Orange temperature */
            margin-right: 15px;
        }
        
        .weather-icon-large {
            font-size: 42px;
            margin-left: 10px;
        }
        
        .weather-description {
            display: flex;
            flex-direction: column;
        }
        
        .weather-condition {
            font-size: 20px;
            font-weight: 500;
            color: #E0E0E0;
        }
        
        .feels-like {
            font-size: 18px;
            color: #D3D3D3;
            margin-top: 4px;
        }
        
        .highlight-metrics-container {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .highlight-metric-card {
            display: flex;
            align-items: center;
            background-color: #233656;  /* Consistent blue */
            border-radius: 8px;
            padding: 10px;
            border: 1px solid rgba(255, 140, 66, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        .highlight-metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(255, 140, 66, 0.2);
        }
        
        .highlight-metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #ff8c42, #ffd700);  /* Sunrise colors */
        }
        
        .metric-icon {
            font-size: 24px;
            margin-right: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 40px;
        }
        
        .metric-details {
            display: flex;
            flex-direction: column;
        }
        
        .metric-value {
            font-size: 20px;
            font-weight: bold;
            color: #ff8c42;  /* Orange values */
        }
        
        .metric-name {
            font-size: 20px; color: #1a1a1a; font-weight: 700;
        }
        
        .section-subtitle {
            font-size: 18px;
            font-weight: 500;
            color: #E0E0E0;
            margin: 15px 0 10px 0;
        }
        
        .metric-card {
            background-color: #2d4b73;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100%;
            transition: transform 0.2s;
            border: 1px solid rgba(255, 140, 66, 0.1);
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(255, 140, 66, 0.2);
        }
        
        .metric-card-icon {
            font-size: 28px;
            margin-bottom: 5px;
        }
        
        .metric-card-label {
            font-size: 14px;
            color: #D3D3D3;
            margin-bottom: 5px;
        }
        
        .metric-card-value {
            font-size: 20px;
            font-weight: bold;
            color: #ff8c42;  /* Orange values */
        }
        
        .metric-card-sublabel {
            font-size: 12px;
            color: #D3D3D3;
            margin-top: 3px;
        }
        .chart-title {
            font-size: 22px;
            font-weight: 600;
            color: #FFFFFF;
            text-align: center;
            margin: 15px 0;
            background-color: #233656;
            padding: 8px;
            border-radius: 6px;
        }
        .weather-details-container {
            background-color: #233656;
            padding: 15px;
            border-radius: 10px;
            margin-top: 15px;
            border: 1px solid rgba(255, 140, 66, 0.15);
        } 
            .highlight-metric-card:nth-child(1) {
            background: linear-gradient(135deg, #233656 0%, #2d4b73 100%);  /* Blue gradient */
            border: 1px solid rgba(255, 140, 66, 0.3);  /* Orange border */
            position: relative;
            overflow: hidden;
        }
        
        .highlight-metric-card:nth-child(1)::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #ff8c42, #ffd700);  /* Sunrise colors */
        }
        
        .highlight-metric-card:nth-child(2) {
            background: linear-gradient(135deg, #233656 0%, #1a2942 100%);  /* Darker blue gradient */
            border: 1px solid rgba(255, 140, 66, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .highlight-metric-card:nth-child(2)::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #ff8c42, #ff6b6b);  /* Sunset colors */
        }
        
        .highlight-metric-card .metric-value {
            color: #ff8c42;  /* Orange text for consistency */
            font-size: 20px;
            font-weight: bold;
        }
        
        .highlight-metric-card .metric-name {
            color: #E0E0E0;  /* Light text for better contrast */
            font-size: 16px;
            font-weight: 500;
        }
            .highlight-metrics-container {
                gap: 15px;  /* Increased gap between cards */
            }
            .highlight-metric-card {
                min-height: 90px;  /* Fixed minimum height */
                padding: 15px;  /* Increased padding */
            }
            .main-weather-card {
                min-height: 210px;  /* Fixed height for main card */
            }
            /* Adjust icon sizes for better balance */
            .metric-icon {
                font-size: 28px;
                min-width: 45px;
            }
            .metric-value {
                font-size: 20px;
            } 
        
        </style>
        """
