import requests
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urljoin, urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
import random

# Set up logging
logger = logging.getLogger(__name__)

SOURCES = {
    "thehindu": {
        "url": "https://www.thehindu.com/news/national/",
        "parser": lambda soup: soup.select('h3.title a, .story-card-news h3 a'),
        "processor": lambda item: item.text.strip(),
        "link_extractor": lambda item, base_url: urljoin(base_url, item.get('href', ''))
    },
    "pib": {
        "url": "https://pib.gov.in/PressReleasePage.aspx",
        "parser": lambda soup: soup.select('.ContentDiv a'),
        "processor": lambda item: re.sub(r'\s+', ' ', item.text).strip(),
        "link_extractor": lambda item, base_url: urljoin(base_url, item.get('href', ''))
    },
    "indianexpress": {
        "url": "https://indianexpress.com/section/india/",
        "parser": lambda soup: soup.select('.articles .title a'),
        "processor": lambda item: item.text.strip(),
        "link_extractor": lambda item, base_url: urljoin(base_url, item.get('href', ''))
    }
}

# Extended sources for geographic filtering
GEOGRAPHIC_SOURCES = {
    "maharashtra": {
        "thehindu_mh": {
            "url": "https://www.thehindu.com/news/national/other-states/",
            "parser": lambda soup: soup.select('h3.title a, .story-card-news h3 a'),
            "processor": lambda item: item.text.strip(),
            "link_extractor": lambda item, base_url: urljoin(base_url, item.get('href', ''))
        },
        "indianexpress_mh": {
            "url": "https://indianexpress.com/section/cities/mumbai/",
            "parser": lambda soup: soup.select('.articles .title a'),
            "processor": lambda item: item.text.strip(),
            "link_extractor": lambda item, base_url: urljoin(base_url, item.get('href', ''))
        }
    },
    "india": {
        "thehindu_national": {
            "url": "https://www.thehindu.com/news/national/",
            "parser": lambda soup: soup.select('h3.title a, .story-card-news h3 a'),
            "processor": lambda item: item.text.strip(),
            "link_extractor": lambda item, base_url: urljoin(base_url, item.get('href', ''))
        },
        "indianexpress_india": {
            "url": "https://indianexpress.com/section/india/",
            "parser": lambda soup: soup.select('.articles .title a'),
            "processor": lambda item: item.text.strip(),
            "link_extractor": lambda item, base_url: urljoin(base_url, item.get('href', ''))
        }
    },
    "world": {
        "thehindu_international": {
            "url": "https://www.thehindu.com/news/international/",
            "parser": lambda soup: soup.select('h3.title a, .story-card-news h3 a'),
            "processor": lambda item: item.text.strip(),
            "link_extractor": lambda item, base_url: urljoin(base_url, item.get('href', ''))
        },
        "indianexpress_world": {
            "url": "https://indianexpress.com/section/world/",
            "parser": lambda soup: soup.select('.articles .title a'),
            "processor": lambda item: item.text.strip(),
            "link_extractor": lambda item, base_url: urljoin(base_url, item.get('href', ''))
        }
    }
}

# UPSC question templates
UPSC_QUESTION_TEMPLATES = [
    "Analyze the implications of {} in the context of Indian governance.",
    "Discuss the role of {} in India's economic development.",
    "Examine the constitutional provisions related to {}.",
    "Evaluate the impact of {} on India's foreign policy.",
    "Critically analyze the government's approach to {}.",
    "Discuss the challenges and opportunities presented by {}.",
    "Examine the environmental implications of {}.",
    "Analyze the social and economic impact of {}.",
    "Discuss the policy measures needed to address {}.",
    "Evaluate the effectiveness of current initiatives related to {}."
]

def create_session():
    """Create a requests session with retry strategy"""
    session = requests.Session()
    
    # Define retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set common headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    return session

def validate_config(config):
    """Validate configuration for news scraping"""
    if not config:
        raise ValueError("Configuration is required")
    
    if not config.get('keywords'):
        raise ValueError("Keywords are required for filtering news")
    
    if not config.get('sources'):
        raise ValueError("At least one news source must be configured")
    
    # Validate that configured sources exist
    invalid_sources = [src for src in config['sources'] if src not in SOURCES]
    if invalid_sources:
        logger.warning(f"Invalid sources configured: {invalid_sources}")

def get_upsc_news(config):
    """
    Fetch UPSC-relevant news from configured sources
    
    Args:
        config (dict): Configuration containing sources, keywords, etc.
        
    Returns:
        list: List of news items matching keywords
        
    Raises:
        ValueError: If configuration is invalid
        requests.RequestException: If network requests fail
    """
    try:
        validate_config(config)
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    
    news_items = []
    keywords = [kw.lower().strip() for kw in config['keywords'] if kw.strip()]
    
    if not keywords:
        logger.warning("No valid keywords found after processing")
        return news_items
    
    session = create_session()
    
    for source in config['sources']:
        if source not in SOURCES:
            logger.warning(f"Skipping unknown source: {source}")
            continue
            
        source_config = SOURCES[source]
        logger.info(f"Scraping news from {source}")
        
        try:
            # Fetch the webpage
            response = session.get(
                source_config["url"], 
                timeout=15,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            items = source_config["parser"](soup)
            
            if not items:
                logger.warning(f"No items found from {source} - selectors may need updating")
                continue
            
            items_processed = 0
            for item in items[:20]:  # Process top 20 items
                try:
                    text = source_config["processor"](item)
                    
                    if not text or len(text.strip()) < 10:
                        continue
                    
                    # Check if any keyword matches
                    text_lower = text.lower()
                    if any(kw in text_lower for kw in keywords):
                        # Extract link
                        link = ""
                        try:
                            link = source_config["link_extractor"](item, source_config["url"])
                        except Exception as link_error:
                            logger.debug(f"Failed to extract link from {source}: {link_error}")
                        
                        news_item = {
                            "source": source.upper(),
                            "title": text[:500],  # Limit title length
                            "link": link,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "category": "general"
                        }
                        news_items.append(news_item)
                        items_processed += 1
                        
                        if items_processed >= 10:  # Limit per source
                            break
                            
                except Exception as item_error:
                    logger.debug(f"Error processing item from {source}: {item_error}")
                    continue
            
            logger.info(f"Successfully processed {items_processed} items from {source}")
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while fetching from {source}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error while fetching from {source}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} while fetching from {source}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while fetching from {source}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error scraping {source}: {e}")
    
    logger.info(f"Total news items found: {len(news_items)}")
    return news_items

def get_weekly_news(config, geography="all"):
    """
    Fetch last week's news with geographic filtering
    
    Args:
        config (dict): Configuration containing keywords, etc.
        geography (str): 'maharashtra', 'india', 'world', or 'all'
        
    Returns:
        dict: Dictionary with news categorized by geography
    """
    logger.info(f"Fetching weekly news for geography: {geography}")
    
    keywords = [kw.lower().strip() for kw in config['keywords'] if kw.strip()]
    session = create_session()
    
    weekly_news = {
        "maharashtra": [],
        "india": [],
        "world": [],
        "summary": {
            "total_articles": 0,
            "date_range": f"{(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}"
        }
    }
    
    # Sample news data for demo (in production, this would fetch from actual sources)
    sample_news = {
        "maharashtra": [
            {"title": "Maharashtra Government Announces New Agricultural Policy", "source": "PIB", "date": "2024-01-15", "link": "https://pib.gov.in/sample1"},
            {"title": "Mumbai Metro Phase 3 Construction Progress Review", "source": "THEHINDU", "date": "2024-01-14", "link": "https://thehindu.com/sample1"},
            {"title": "Digital Maharashtra Initiative Launched", "source": "INDIANEXPRESS", "date": "2024-01-13", "link": "https://indianexpress.com/sample1"},
            {"title": "Pune Smart City Mission Updates", "source": "PIB", "date": "2024-01-12", "link": "https://pib.gov.in/sample2"},
            {"title": "Maharashtra Water Conservation Programs", "source": "THEHINDU", "date": "2024-01-11", "link": "https://thehindu.com/sample2"},
        ],
        "india": [
            {"title": "Union Budget 2024: Key Highlights for Economic Growth", "source": "PIB", "date": "2024-01-15", "link": "https://pib.gov.in/sample3"},
            {"title": "Digital India Mission Achieves Major Milestone", "source": "THEHINDU", "date": "2024-01-14", "link": "https://thehindu.com/sample3"},
            {"title": "Supreme Court Ruling on Environmental Protection", "source": "INDIANEXPRESS", "date": "2024-01-13", "link": "https://indianexpress.com/sample2"},
            {"title": "New Education Policy Implementation Progress", "source": "PIB", "date": "2024-01-12", "link": "https://pib.gov.in/sample4"},
            {"title": "India's Space Mission Success", "source": "THEHINDU", "date": "2024-01-11", "link": "https://thehindu.com/sample4"},
            {"title": "Healthcare Infrastructure Development", "source": "INDIANEXPRESS", "date": "2024-01-10", "link": "https://indianexpress.com/sample3"},
        ],
        "world": [
            {"title": "India-US Strategic Partnership Strengthened", "source": "THEHINDU", "date": "2024-01-15", "link": "https://thehindu.com/sample5"},
            {"title": "Climate Change Conference: India's Position", "source": "INDIANEXPRESS", "date": "2024-01-14", "link": "https://indianexpress.com/sample4"},
            {"title": "G20 Summit Preparations and India's Role", "source": "PIB", "date": "2024-01-13", "link": "https://pib.gov.in/sample5"},
            {"title": "International Trade Agreements Impact", "source": "THEHINDU", "date": "2024-01-12", "link": "https://thehindu.com/sample6"},
            {"title": "Global Technology Partnerships", "source": "INDIANEXPRESS", "date": "2024-01-11", "link": "https://indianexpress.com/sample5"},
        ]
    }
    
    # Filter by geography
    if geography == "all":
        for geo in ["maharashtra", "india", "world"]:
            weekly_news[geo] = sample_news[geo]
    else:
        weekly_news[geography] = sample_news.get(geography, [])
    
    # Calculate summary
    total_articles = sum(len(articles) for articles in weekly_news.values() if isinstance(articles, list))
    weekly_news["summary"]["total_articles"] = total_articles
    
    return weekly_news

def get_monthly_news(config):
    """
    Fetch top monthly news
    
    Args:
        config (dict): Configuration containing keywords, etc.
        
    Returns:
        list: List of top monthly news items
    """
    logger.info("Fetching monthly top news")
    
    # Sample monthly news data (in production, this would fetch from actual sources)
    monthly_news = [
        {
            "title": "Economic Survey 2024: India's Growth Trajectory",
            "source": "PIB",
            "date": "2024-01-01",
            "link": "https://pib.gov.in/monthly1",
            "category": "economy",
            "importance": "high",
            "summary": "Comprehensive analysis of India's economic performance and future outlook."
        },
        {
            "title": "Constitutional Amendment Bill Passed",
            "source": "THEHINDU",
            "date": "2024-01-05",
            "link": "https://thehindu.com/monthly1",
            "category": "governance",
            "importance": "high",
            "summary": "Major constitutional changes affecting federal structure."
        },
        {
            "title": "National Education Policy: Implementation Report",
            "source": "INDIANEXPRESS",
            "date": "2024-01-08",
            "link": "https://indianexpress.com/monthly1",
            "category": "education",
            "importance": "high",
            "summary": "Progress report on NEP implementation across states."
        },
        {
            "title": "Climate Action Plan: India's Commitment",
            "source": "PIB",
            "date": "2024-01-10",
            "link": "https://pib.gov.in/monthly2",
            "category": "environment",
            "importance": "high",
            "summary": "India's comprehensive climate action strategy."
        },
        {
            "title": "Digital Infrastructure Development",
            "source": "THEHINDU",
            "date": "2024-01-12",
            "link": "https://thehindu.com/monthly2",
            "category": "technology",
            "importance": "high",
            "summary": "Major digital infrastructure projects launched."
        },
        {
            "title": "Healthcare Reforms: Universal Coverage",
            "source": "INDIANEXPRESS",
            "date": "2024-01-14",
            "link": "https://indianexpress.com/monthly2",
            "category": "health",
            "importance": "high",
            "summary": "New healthcare policy for universal coverage."
        }
    ]
    
    return monthly_news

def generate_upsc_questions(config):
    """
    Generate UPSC-relevant questions based on recent news
    
    Args:
        config (dict): Configuration containing keywords, etc.
        
    Returns:
        list: List of UPSC questions with context
    """
    logger.info("Generating UPSC questions from recent news")
    
    # Sample UPSC questions based on current affairs
    upsc_questions = [
        {
            "question": "Analyze the implications of digital governance initiatives in improving public service delivery in India.",
            "topic": "Digital Governance",
            "difficulty": "medium",
            "source_news": "Digital India Mission Achieves Major Milestone",
            "context": "Recent developments in digital infrastructure and e-governance platforms",
            "answer_hints": ["Digital divide", "Cybersecurity", "Rural connectivity", "Skill development"],
            "date": "2024-01-15"
        },
        {
            "question": "Examine the constitutional provisions related to environmental protection and their implementation challenges.",
            "topic": "Environment & Constitution",
            "difficulty": "high",
            "source_news": "Supreme Court Ruling on Environmental Protection",
            "context": "Recent judicial interventions in environmental matters",
            "answer_hints": ["Article 21", "Directive Principles", "Judicial activism", "Pollution control"],
            "date": "2024-01-14"
        },
        {
            "question": "Discuss the role of international partnerships in India's space program development.",
            "topic": "International Relations & Space",
            "difficulty": "medium",
            "source_news": "India's Space Mission Success",
            "context": "Recent achievements in space technology and international collaborations",
            "answer_hints": ["ISRO achievements", "Commercial space", "International cooperation", "Technology transfer"],
            "date": "2024-01-13"
        },
        {
            "question": "Evaluate the effectiveness of New Education Policy in addressing educational inequalities.",
            "topic": "Education Policy",
            "difficulty": "high",
            "source_news": "New Education Policy Implementation Progress",
            "context": "Progress and challenges in NEP implementation",
            "answer_hints": ["Access to education", "Quality improvement", "Digital divide", "Teacher training"],
            "date": "2024-01-12"
        },
        {
            "question": "Analyze the impact of climate change policies on India's economic development.",
            "topic": "Environment & Economy",
            "difficulty": "high",
            "source_news": "Climate Action Plan: India's Commitment",
            "context": "Balance between environmental protection and economic growth",
            "answer_hints": ["Sustainable development", "Green economy", "Energy transition", "Carbon neutrality"],
            "date": "2024-01-11"
        },
        {
            "question": "Critically examine the challenges in implementing universal healthcare coverage in India.",
            "topic": "Healthcare Policy",
            "difficulty": "medium",
            "source_news": "Healthcare Reforms: Universal Coverage",
            "context": "Recent healthcare policy reforms and implementation challenges",
            "answer_hints": ["Public health infrastructure", "Health financing", "Rural healthcare", "Digital health"],
            "date": "2024-01-10"
        },
        {
            "question": "Discuss the implications of federal structure in policy implementation across Indian states.",
            "topic": "Federalism",
            "difficulty": "high",
            "source_news": "Constitutional Amendment Bill Passed",
            "context": "Recent constitutional changes and their impact on federal relations",
            "answer_hints": ["Centre-state relations", "Cooperative federalism", "Policy coordination", "Regional disparities"],
            "date": "2024-01-09"
        },
        {
            "question": "Examine the role of technology in transforming agricultural practices in India.",
            "topic": "Agriculture & Technology",
            "difficulty": "medium",
            "source_news": "Maharashtra Government Announces New Agricultural Policy",
            "context": "Technological interventions in agriculture and farmer welfare",
            "answer_hints": ["Precision farming", "Digital agriculture", "Farmer income", "Sustainable agriculture"],
            "date": "2024-01-08"
        },
        {
            "question": "Analyze the importance of urban planning in sustainable city development.",
            "topic": "Urban Governance",
            "difficulty": "medium",
            "source_news": "Mumbai Metro Phase 3 Construction Progress Review",
            "context": "Urban infrastructure development and planning challenges",
            "answer_hints": ["Smart cities", "Public transportation", "Urban sprawl", "Sustainable development"],
            "date": "2024-01-07"
        },
        {
            "question": "Evaluate India's strategic partnerships in shaping its foreign policy objectives.",
            "topic": "International Relations",
            "difficulty": "high",
            "source_news": "India-US Strategic Partnership Strengthened",
            "context": "Recent developments in bilateral and multilateral relations",
            "answer_hints": ["Strategic autonomy", "Multi-alignment", "Economic diplomacy", "Security cooperation"],
            "date": "2024-01-06"
        },
        {
            "question": "Discuss the challenges and opportunities in India's renewable energy transition.",
            "topic": "Energy Policy",
            "difficulty": "medium",
            "source_news": "Climate Action Plan: India's Commitment",
            "context": "India's commitment to renewable energy and climate goals",
            "answer_hints": ["Solar energy", "Wind power", "Energy security", "Grid integration"],
            "date": "2024-01-05"
        },
        {
            "question": "Examine the role of judiciary in protecting fundamental rights in the digital age.",
            "topic": "Constitutional Law",
            "difficulty": "high",
            "source_news": "Supreme Court Ruling on Environmental Protection",
            "context": "Judicial interventions in protecting rights and environment",
            "answer_hints": ["Right to privacy", "Environmental justice", "Digital rights", "Judicial review"],
            "date": "2024-01-04"
        }
    ]
    
    return upsc_questions

def test_sources():
    """Test function to check if sources are accessible"""
    session = create_session()
    results = {}
    
    for source_name, source_config in SOURCES.items():
        try:
            response = session.get(source_config["url"], timeout=10)
            response.raise_for_status()
            results[source_name] = {
                "status": "OK",
                "status_code": response.status_code,
                "content_length": len(response.content)
            }
        except Exception as e:
            results[source_name] = {
                "status": "ERROR",
                "error": str(e)
            }
    
    return results