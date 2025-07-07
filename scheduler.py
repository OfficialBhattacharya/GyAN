from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime
import logging
from email_manager import send_news_email
from news_scraper import get_upsc_news

# Set up logging
logger = logging.getLogger(__name__)

def schedule_daily_email(config):
    """
    Set up a background scheduler for daily news email delivery
    
    Args:
        config (dict): Configuration containing send_time and other settings
        
    Returns:
        BackgroundScheduler: Configured and started scheduler
        
    Raises:
        ValueError: If configuration is invalid
        Exception: If scheduler fails to start
    """
    try:
        # Validate configuration
        if not config:
            raise ValueError("Configuration is required")
        
        send_time = config.get('send_time', '07:00')
        if ':' not in send_time:
            raise ValueError(f"Invalid send_time format: {send_time}. Expected HH:MM")
        
        try:
            hour, minute = map(int, send_time.split(':'))
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                raise ValueError(f"Invalid time values: {hour}:{minute}")
        except ValueError as e:
            raise ValueError(f"Invalid send_time format: {send_time}. {e}")
        
        # Configure scheduler with custom executor
        executors = {
            'default': ThreadPoolExecutor(max_workers=2)
        }
        
        job_defaults = {
            'coalesce': True,  # Combine multiple pending instances of the same job
            'max_instances': 1,  # Only allow one instance of each job to run at a time
            'misfire_grace_time': 300  # Allow 5 minutes grace time for delayed execution
        }
        
        scheduler = BackgroundScheduler(
            executors=executors,
            job_defaults=job_defaults
        )
        
        def news_email_job():
            """Job function to fetch news and send email"""
            job_start_time = datetime.now()
            logger.info(f"Starting scheduled news email job at {job_start_time}")
            
            try:
                # Check if email is configured
                if not config.get('email') or not config.get('smtp_username'):
                    logger.warning("Email not configured - skipping news email job")
                    return
                
                # Fetch news
                logger.info("Fetching UPSC news...")
                news_items = get_upsc_news(config)
                
                if not news_items:
                    logger.warning("No news items found matching keywords")
                    return
                
                logger.info(f"Found {len(news_items)} news items, sending email...")
                
                # Send email
                send_news_email(config, news_items)
                
                job_duration = datetime.now() - job_start_time
                logger.info(f"News email job completed successfully in {job_duration.total_seconds():.2f} seconds")
                
            except Exception as e:
                logger.error(f"News email job failed: {e}", exc_info=True)
                # Don't re-raise to prevent scheduler from stopping
        
        # Add the job
        job = scheduler.add_job(
            news_email_job,
            'cron',
            hour=hour,
            minute=minute,
            id='daily_news_email',
            name='Daily UPSC News Email',
            replace_existing=True
        )
        
        logger.info(f"Scheduled daily news email job for {send_time} (Job ID: {job.id})")
        
        # Start scheduler
        scheduler.start()
        logger.info("News email scheduler started successfully")
        
        return scheduler
        
    except Exception as e:
        logger.error(f"Failed to create scheduler: {e}")
        raise

def get_scheduler_status(scheduler):
    """
    Get current status of the scheduler and jobs
    
    Args:
        scheduler: The BackgroundScheduler instance
        
    Returns:
        dict: Status information about scheduler and jobs
    """
    if not scheduler:
        return {"status": "not_initialized"}
    
    try:
        jobs = scheduler.get_jobs()
        job_info = []
        
        for job in jobs:
            next_run = job.next_run_time
            job_info.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "status": "running" if scheduler.running else "stopped",
            "jobs": job_info,
            "job_count": len(jobs)
        }
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return {"status": "error", "error": str(e)}