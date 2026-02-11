"""
Jobs API endpoints
Provides job status and monitoring endpoints
"""
from flask import Blueprint, request
from utils.decorators import handle_errors
from api.middleware.auth import require_auth
from utils.response import APIResponse
from database.db_manager import DatabaseManager
from database.repositories.job_repository import JobRepository

jobs_bp = Blueprint('jobs', __name__, url_prefix='/api/v1/jobs')


@jobs_bp.route('', methods=['GET'])
@handle_errors
@require_auth
def get_jobs():
    """
    Get jobs with optional filters
    
    Query params:
        job_type: Filter by job type (e.g., auto_training, pattern_learning)
        status: Filter by status (comma-separated: pending,processing,completed,failed)
        limit: Limit results (default: 100)
    
    Returns:
        200: List of jobs
        401: Unauthorized
    """
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        db = DatabaseManager()
        
        # Get query parameters
        job_type = request.args.get('job_type', '')
        status_filter = request.args.get('status', '')
        limit = request.args.get('limit', 100, type=int)
        
        logger.info(f"Jobs query: job_type={job_type}, status={status_filter}, limit={limit}")
        
        # Parse status filter
        statuses = [s.strip() for s in status_filter.split(',') if s.strip()] if status_filter else None
        
        # Build query
        conn = db.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []
        
        if job_type:
            query += " AND type = ?"  # Column name is 'type', not 'job_type'
            params.append(job_type)
        
        if statuses:
            placeholders = ','.join(['?' for _ in statuses])
            query += f" AND status IN ({placeholders})"
            params.extend(statuses)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        logger.info(f"Executing query: {query} with params: {params}")
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        logger.info(f"Found {len(rows)} jobs")
        
        # Convert to dict and parse payload JSON
        jobs = []
        for row in rows:
            try:
                job = dict(row)
                # Parse payload if it's a JSON string
                if job.get('payload') and isinstance(job['payload'], str):
                    try:
                        job['payload'] = json.loads(job['payload'])
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse payload for job {job.get('id')}: {e}")
                        # Keep as string if parsing fails
                jobs.append(job)
            except Exception as e:
                logger.error(f"Error processing job row: {e}")
                continue
        
        return APIResponse.success(
            data={
                'jobs': jobs,
                'count': len(jobs)
            },
            message=f"Retrieved {len(jobs)} jobs"
        )
    except Exception as e:
        logger.error(f"Error in get_jobs: {e}", exc_info=True)
        return APIResponse.error(f"Failed to retrieve jobs: {str(e)}", 500)


@jobs_bp.route('/<int:job_id>', methods=['GET'])
@handle_errors
@require_auth
def get_job(job_id):
    """
    Get job details by ID
    
    Returns:
        200: Job details
        404: Job not found
        401: Unauthorized
    """
    db = DatabaseManager()
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return APIResponse.error("Job not found", 404)
    
    job = dict(row)
    
    return APIResponse.success(
        data={'job': job},
        message="Job retrieved successfully"
    )
