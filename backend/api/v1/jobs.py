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
        template_id: Filter by template ID
        status: Filter by status (comma-separated: pending,running,completed,failed)
        limit: Limit results (default: 10)
    
    Returns:
        200: List of jobs
        401: Unauthorized
    """
    
    db = DatabaseManager()
    job_repo = JobRepository(db)
    
    # Get query parameters
    template_id = request.args.get('template_id', type=int)
    status_filter = request.args.get('status', '')
    limit = request.args.get('limit', 10, type=int)
    
    # Parse status filter
    statuses = [s.strip() for s in status_filter.split(',') if s.strip()] if status_filter else None
    
    # Build query
    conn = db.get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []
    
    if template_id:
        query += " AND template_id = ?"
        params.append(template_id)
    
    if statuses:
        placeholders = ','.join(['?' for _ in statuses])
        query += f" AND status IN ({placeholders})"
        params.extend(statuses)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    jobs = [dict(row) for row in rows]
    
    return APIResponse.success(
        data={
            'jobs': jobs,
            'count': len(jobs)
        },
        message=f"Retrieved {len(jobs)} jobs"
    )


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
