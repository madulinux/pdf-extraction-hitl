"""
Extraction API Routes
Document extraction endpoints (using core services)
"""

from flask import Blueprint, request, current_app, send_file

from core.extraction.services import ExtractionService
from core.export.excel_exporter import ExcelExporter
from database.repositories.document_repository import DocumentRepository
from database.repositories.feedback_repository import FeedbackRepository
from database.repositories.template_repository import TemplateRepository
from database.repositories.training_repository import TrainingRepository
from utils.response import APIResponse
from utils.decorators import handle_errors
from api.middleware.auth import require_auth
from shared.exceptions import ValidationError, NotFoundError
from database.db_manager import DatabaseManager
import os
from datetime import datetime


# Create blueprint
extraction_bp = Blueprint("extraction_v1", __name__, url_prefix="/api/v1/extraction")


def get_extraction_service():
    """Get extraction service instance"""
    db_path = os.getenv("DATABASE_PATH", "data/app.db")
    db = DatabaseManager(db_path)
    document_repo = DocumentRepository(db)
    feedback_repo = FeedbackRepository(db)
    template_repo = TemplateRepository(db)
    training_repo = TrainingRepository(db)
    return ExtractionService(
        document_repo=document_repo,
        feedback_repo=feedback_repo,
        template_repo=template_repo,
        training_repo=training_repo,
        upload_folder=current_app.config["UPLOAD_FOLDER"],
        model_folder=current_app.config["MODEL_FOLDER"],
        feedback_folder=current_app.config["FEEDBACK_FOLDER"],
    )


@extraction_bp.route("/extract", methods=["POST"])
@handle_errors
@require_auth
def extract_document():
    """
    Extract data from filled PDF document

    Request: multipart/form-data
    - file: PDF file
    - template_id: Template ID
    - experiment_phase: (Optional) Experiment phase ('baseline', 'adaptive', or omit for production)

    Returns:
        200: Extraction successful
        400: Validation error
        401: Unauthorized
    """
    # Validate file
    if "file" not in request.files:
        return APIResponse.bad_request("No file provided")

    file = request.files["file"]
    template_id = request.form.get("template_id")
    experiment_phase = request.form.get("experiment_phase", 'adaptive')  # NEW: Optional experiment phase

    if not template_id:
        return APIResponse.bad_request("Template ID is required")

    if file.filename == "":
        return APIResponse.bad_request("No file selected")

    if not file.filename.lower().endswith(".pdf"):
        return APIResponse.bad_request("Only PDF files are allowed")

    # Extract document (config will be loaded from DB or JSON automatically)
    service = get_extraction_service()
    template = service.template_repo.find_by_id(int(template_id))

    if not template:
        return APIResponse.not_found(f"Template with ID {template_id} not found")

    try:
        result = service.extract_document(
            file=file,
            template_id=int(template_id),
            template_config_path=template.config_path,
            experiment_phase=experiment_phase,  # NEW: Pass experiment phase
        )

        return APIResponse.success(result, "Data extracted successfully")

    except NotFoundError as e:
        return APIResponse.not_found(str(e))
    except Exception as e:
        return APIResponse.internal_error(f"Extraction failed: {str(e)}")


@extraction_bp.route("/extract/bulk", methods=["POST"])
@handle_errors
@require_auth
def extract_documents_bulk():
    """
    Extract data from multiple PDF documents in bulk

    Request: multipart/form-data
    - files: Multiple PDF files
    - template_id: Template ID
    - experiment_phase: (Optional) Experiment phase ('baseline', 'adaptive', or omit for production)

    Returns:
        200: Bulk extraction results
        400: Validation error
        401: Unauthorized
    """
    # Validate files
    if "files" not in request.files:
        return APIResponse.bad_request("No files provided")

    files = request.files.getlist("files")
    template_id = request.form.get("template_id")
    experiment_phase = request.form.get("experiment_phase", 'adaptive')

    if not template_id:
        return APIResponse.bad_request("Template ID is required")

    if not files or len(files) == 0:
        return APIResponse.bad_request("No files selected")

    # Validate all files are PDFs
    for file in files:
        if file.filename == "":
            return APIResponse.bad_request("Empty filename detected")
        if not file.filename.lower().endswith(".pdf"):
            return APIResponse.bad_request(f"File {file.filename} is not a PDF")

    # Extract documents in bulk
    service = get_extraction_service()
    template = service.template_repo.find_by_id(int(template_id))

    if not template:
        return APIResponse.not_found(f"Template with ID {template_id} not found")

    try:
        result = service.extract_documents_bulk(
            files=files,
            template_id=int(template_id),
            template_config_path=template.config_path,
            experiment_phase=experiment_phase,
        )

        return APIResponse.success(
            result,
            f"Bulk extraction completed: {result['successful']} successful, {result['failed']} failed"
        )

    except NotFoundError as e:
        return APIResponse.not_found(str(e))
    except Exception as e:
        return APIResponse.internal_error(f"Bulk extraction failed: {str(e)}")


@extraction_bp.route("/validate", methods=["POST"])
@handle_errors
@require_auth
def validate_corrections():
    """
    Save user corrections as feedback and trigger adaptive learning

    Request Body:
    {
        "document_id": int,
        "corrections": {...}
    }

    Returns:
        200: Corrections saved
        400: Validation error
        401: Unauthorized
    """
    # 🐛 CRITICAL DEBUG: Log at very start of endpoint
    current_app.logger.info("=" * 100)
    current_app.logger.info("🚨 VALIDATE ENDPOINT CALLED - CODE VERSION 2.0")
    current_app.logger.info("=" * 100)
    
    data = request.get_json()

    if not data:
        return APIResponse.bad_request("Request body is required")

    if "document_id" not in data or "corrections" not in data:
        return APIResponse.bad_request("document_id and corrections are required")

    service = get_extraction_service()

    try:
        # Save corrections (returns all_fields + corrected_fields)
        result = service.save_corrections(
            document_id=data["document_id"], corrections=data["corrections"]
        )

        # 🐛 DEBUG: Log at start of auto-training section
        current_app.logger.info("=" * 80)
        current_app.logger.info("🔍 FEEDBACK VALIDATION - CHECKING AUTO-TRAINING CONFIG")
        current_app.logger.info("=" * 80)
        
        auto_training = current_app.config.get('AUTO_TRAINING', True)
        if auto_training:
            # Check if async mode is enabled for learning and training separately
            async_learning = current_app.config.get('ASYNC_PATTERN_LEARNING', True)
            async_training = current_app.config.get('ASYNC_AUTO_TRAINING', True)
            
            # 🐛 DEBUG: Log config values with types
            current_app.logger.info(
                f"🔧 Config: AUTO_TRAINING={auto_training} (type={type(auto_training).__name__}), "
                f"ASYNC_PATTERN_LEARNING={async_learning} (type={type(async_learning).__name__}), "
                f"ASYNC_AUTO_TRAINING={async_training} (type={type(async_training).__name__})"
            )
            current_app.logger.info(f"🔧 Will use {'ASYNC' if async_training else 'SYNC'} training mode")
            
            # ✅ IMPORTANT: Pattern learning and training are independent
            # - Pattern learning can be async (background thread)
            # - Training can be async (job queue) or sync (immediate)
            
            # ========================================
            # PATTERN LEARNING (Async or Sync)
            # ========================================
            if async_learning:
                # ⚡ ASYNC: Run pattern learning in background thread
                import threading
                
                document_id = data["document_id"]
                all_fields = result.get("all_fields", {})
                corrected_fields = result.get("corrected_fields", {})
                app = current_app._get_current_object()
                
                def run_pattern_learning():
                    """Background thread for pattern learning only"""
                    with app.app_context():
                        try:
                            from core.learning.services import ModelService
                            learning_service = ModelService()
                            learning_result = learning_service.trigger_adaptive_learning(
                                document_id=document_id,
                                all_fields=all_fields,
                                corrected_fields=corrected_fields,
                            )
                            app.logger.debug(
                                f"✅ Pattern learning: {learning_result['summary']['triggered']} fields triggered"
                            )
                        except Exception as e:
                            app.logger.warning(f"Pattern learning failed: {e}")
                
                thread = threading.Thread(target=run_pattern_learning, daemon=True)
                thread.start()
                
                result["learning"] = {
                    "status": "scheduled",
                    "message": "Pattern learning scheduled in background",
                    "mode": "async"
                }
            else:
                # 🔄 SYNC: Run pattern learning immediately
                try:
                    from core.learning.services import ModelService
                    learning_service = ModelService()
                    learning_result = learning_service.trigger_adaptive_learning(
                        document_id=data["document_id"],
                        all_fields=result.get("all_fields", {}),
                        corrected_fields=result.get("corrected_fields", {}),
                    )
                    result["learning"] = {
                        **learning_result,
                        "mode": "sync"
                    }
                except Exception as e:
                    current_app.logger.warning(f"Pattern learning failed: {e}")
                    result["learning"] = {"status": "failed", "error": str(e)}
            
            # ========================================
            # AUTO-TRAINING (Async via Job Queue or Sync)
            # ========================================
            if async_training:
                # ⚡ ASYNC: Enqueue training job to worker
                current_app.logger.info("🚀 Entering ASYNC training mode - will enqueue job to worker")
                try:
                    from database.repositories.document_repository import DocumentRepository
                    from database.repositories.job_repository import JobRepository
                    from database.db_manager import DatabaseManager
                    
                    db = DatabaseManager()
                    doc_repo = DocumentRepository(db)
                    document = doc_repo.find_by_id(data["document_id"])
                    
                    if document:
                        template_id = document.template_id
                        model_folder = current_app.config['MODEL_FOLDER']
                        job_repo = JobRepository(db)
                        
                        # Check if model exists (first training or incremental)
                        import os
                        model_path = os.path.join(model_folder, f"template_{template_id}_model.joblib")
                        is_first_training = not os.path.exists(model_path)
                        
                        # ✅ PRE-CHECK: Only enqueue if conditions are met
                        min_new_docs = current_app.config.get('MIN_NEW_DOCUMENTS', 5)
                        
                        # Count validated documents not yet used for training
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT COUNT(*)
                            FROM documents
                            WHERE template_id = ? 
                              AND status = 'validated'
                              AND used_for_training = 0
                        ''', (template_id,))
                        unused_docs = cursor.fetchone()[0]
                        conn.close()
                        
                        # Check if there is already a pending/running job
                        has_active_job = job_repo.has_active_auto_training_job(template_id)
                        current_app.logger.info(f"🔍 Active job check: has_active_job={has_active_job}")
                        
                        if not has_active_job:
                            # ✅ FIRST TRAINING: Enqueue immediately if model doesn't exist
                            # ✅ INCREMENTAL: Enqueue only if min_new_docs threshold met
                            should_enqueue = is_first_training or (unused_docs >= min_new_docs)
                            current_app.logger.info(
                                f"🔍 Enqueue decision: is_first_training={is_first_training}, "
                                f"unused_docs={unused_docs}, min_new_docs={min_new_docs}, "
                                f"should_enqueue={should_enqueue}"
                            )
                            
                            if should_enqueue:
                                job_id = job_repo.enqueue_auto_training_job(template_id, model_folder, is_first_training)
                                training_type = "first training" if is_first_training else "incremental training"
                                current_app.logger.info(
                                    f"📥 Enqueued {training_type} job {job_id} for template {template_id} ({unused_docs} unused docs)"
                                )
                                result["auto_training"] = {
                                    "status": "enqueued",
                                    "job_id": job_id,
                                    "message": f"{training_type.capitalize()} job enqueued ({unused_docs} unused docs)",
                                    "mode": "async",
                                    "is_first_training": is_first_training
                                }
                            else:
                                current_app.logger.debug(
                                    f"⏭️  Skipped enqueue for template {template_id} - only {unused_docs}/{min_new_docs} unused docs"
                                )
                                result["auto_training"] = {
                                    "status": "skipped",
                                    "message": f"Not enough documents ({unused_docs}/{min_new_docs})",
                                    "mode": "async"
                                }
                        else:
                            current_app.logger.info(
                                f"⏭️  Skipped auto-training enqueue for template {template_id} - job already active"
                            )
                            result["auto_training"] = {
                                "status": "skipped",
                                "message": "Training job already active",
                                "mode": "async"
                            }
                except Exception as e:
                    current_app.logger.error(f"❌ Auto-training scheduling failed: {e}")
                    current_app.logger.error(f"❌ Exception type: {type(e).__name__}")
                    import traceback
                    current_app.logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    result["auto_training"] = {"status": "failed", "error": str(e), "mode": "async"}
                    # ⚠️ DO NOT FALLBACK TO SYNC - return error instead
                    return APIResponse.success(result, "Corrections saved but auto-training scheduling failed")
            else:
                # 🔄 SYNC: Run training immediately (blocking)
                current_app.logger.warning("⚠️  Using SYNC training mode - training will block API request!")
                try:
                    from core.learning.auto_trainer import get_auto_training_service
                    from database.repositories.document_repository import DocumentRepository
                    from database.db_manager import DatabaseManager
                    
                    db = DatabaseManager()
                    doc_repo = DocumentRepository(db)
                    document = doc_repo.find_by_id(data["document_id"])
                    
                    if document:
                        template_id = document.template_id
                        model_folder = current_app.config['MODEL_FOLDER']
                        auto_trainer = get_auto_training_service(db)
                        model_path = os.path.join(model_folder, f"template_{template_id}_model.joblib")
                        is_first_training = not os.path.exists(model_path)
                        training_result = auto_trainer.check_and_train(
                            template_id=template_id,
                            model_folder=model_folder,
                            force_first_training=is_first_training
                        )
                        
                        if training_result:
                            result["auto_training"] = {
                                "status": "completed",
                                "training_samples": training_result['training_samples'],
                                "accuracy": training_result['test_metrics']['accuracy'],
                                "mode": "sync"
                            }
                        else:
                            result["auto_training"] = {
                                "status": "skipped",
                                "message": "Training conditions not met",
                                "mode": "sync"
                            }
                except Exception as e:
                    current_app.logger.warning(f"Auto-training failed: {e}")
                    result["auto_training"] = {"status": "failed", "error": str(e), "mode": "sync"}
        else:
            current_app.logger.info("Auto-training disabled")

        
        return APIResponse.success(result, "Corrections saved successfully")

    except NotFoundError as e:
        return APIResponse.not_found(str(e))


@extraction_bp.route("/documents", methods=["GET"])
@handle_errors
@require_auth
def list_documents():
    """
    Get all documents

    Returns:
        200: List of documents
        401: Unauthorized
    """

    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 10, type=int)
    search = request.args.get("search", None)
    template_id = request.args.get("template_id", None)
    status = request.args.get("status", None)

    service = get_extraction_service()
    documents, meta = service.get_all_documents(page, page_size, search, template_id, status)

    return APIResponse.success(
        data={"documents": documents},
        message="Documents retrieved successfully",
        meta=meta,
    )


@extraction_bp.route("/documents/<int:document_id>", methods=["GET"])
@handle_errors
@require_auth
def get_document(document_id):
    """
    Get document by ID

    Returns:
        200: Document details
        404: Document not found
        401: Unauthorized
    """
    service = get_extraction_service()
    document = service.get_document_by_id(document_id)

    if not document:
        return APIResponse.not_found(f"Document with ID {document_id} not found")

    return APIResponse.success(
        data={"document": document}, message="Document retrieved successfully"
    )


@extraction_bp.route("/documents/<int:document_id>/preview", methods=["GET"])
@handle_errors
@require_auth
def preview_document(document_id):
    """
    Get document PDF for preview

    Returns:
        200: PDF file
        404: Document not found
        401: Unauthorized
    """
    from flask import send_file

    service = get_extraction_service()
    document = service.get_document_by_id(document_id)

    if not document:
        return APIResponse.not_found(f"Document with ID {document_id} not found")

    file_path = document.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return APIResponse.not_found("Document file not found")

    return send_file(
        file_path,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=document.get("filename", "document.pdf"),
    )


@extraction_bp.route("/export/<int:template_id>", methods=["GET"])
@handle_errors
@require_auth
def export_extraction_results(template_id):
    """
    Export extraction results to Excel for a specific template
    
    Query Parameters:
        status: Filter by status (optional: 'validated', 'pending', 'all')
        include_metadata: Include summary sheet (default: true)
    
    Returns:
        200: Excel file download
        404: Template not found
        401: Unauthorized
    """
    db_path = os.getenv("DATABASE_PATH", "data/app.db")
    db = DatabaseManager(db_path)
    doc_repo = DocumentRepository(db)
    template_repo = TemplateRepository(db)
    
    # Get template info
    template = template_repo.find_by_id(template_id)
    if not template:
        return APIResponse.not_found(f"Template with ID {template_id} not found")
    template = template.to_dict()
    # Get query parameters
    status_filter = request.args.get('status', 'all')
    include_metadata = request.args.get('include_metadata', 'true').lower() == 'true'
    
    # Get documents for this template
    conn = db.get_connection()
    cursor = conn.cursor()
    
    if status_filter == 'all':
        cursor.execute('''
            SELECT * FROM documents 
            WHERE template_id = ?
            ORDER BY created_at DESC
        ''', (template_id,))
    else:
        cursor.execute('''
            SELECT * FROM documents 
            WHERE template_id = ? AND status = ?
            ORDER BY created_at DESC
        ''', (template_id, status_filter))
    
    columns = [description[0] for description in cursor.description]
    documents = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    if not documents:
        conn.close()
        return APIResponse.not_found("No documents found for this template")

    # Fetch feedback in bulk so export reflects corrected values when available
    document_ids = [doc.get('id') for doc in documents if doc.get('id') is not None]
    feedback_by_doc: dict = {}
    if document_ids:
        placeholders = ",".join(["?"] * len(document_ids))
        cursor.execute(
            f"""
            SELECT document_id, field_name, corrected_value
            FROM feedback
            WHERE document_id IN ({placeholders})
            """,
            tuple(document_ids),
        )
        for row in cursor.fetchall():
            doc_id = row[0]
            field_name = row[1]
            corrected_value = row[2]
            if doc_id not in feedback_by_doc:
                feedback_by_doc[doc_id] = {}
            feedback_by_doc[doc_id][field_name] = corrected_value

    for doc in documents:
        doc['feedback_values'] = feedback_by_doc.get(doc.get('id'), {})
    
    # Get field names from database (field_configs table) BEFORE closing connection
    cursor.execute('''
        SELECT fc.field_name 
        FROM field_configs fc
        JOIN template_configs tc ON fc.config_id = tc.id
        WHERE tc.template_id = ?
        ORDER BY fc.extraction_order, fc.field_name
    ''', (template_id,))
    field_names = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Parse extraction results
    import json
    for doc in documents:
        if doc.get('extraction_result'):
            try:
                extraction_result = json.loads(doc['extraction_result'])
                doc['extraction_result'] = extraction_result
                
                # Debug: Log structure (only first document to avoid spam)
                if doc.get('id') == documents[0].get('id'):
                    current_app.logger.warning(f"🔍 EXPORT DEBUG - Document {doc.get('id')} structure:")
                    current_app.logger.warning(f"  - Top level keys: {list(extraction_result.keys())}")
                    if 'extracted_data' in extraction_result:
                        extracted_data = extraction_result['extracted_data']
                        current_app.logger.warning(f"  - extracted_data has {len(extracted_data)} fields")
                        current_app.logger.warning(f"  - Sample fields: {list(extracted_data.keys())[:5]}")
                        current_app.logger.warning(f"  - Sample values: {dict(list(extracted_data.items())[:3])}")
                    else:
                        current_app.logger.warning(f"  - No extracted_data key! Direct fields: {list(extraction_result.keys())[:5]}")
            except (json.JSONDecodeError, TypeError) as e:
                current_app.logger.error(f"Failed to parse extraction_result for doc {doc.get('id')}: {e}")
                doc['extraction_result'] = {}
    
    current_app.logger.warning(f"📊 EXPORT: {len(documents)} documents, {len(field_names)} fields: {field_names}")
    
    # Create Excel file
    exporter = ExcelExporter()
    excel_file = exporter.export_extraction_results(
        documents=documents,
        template_name=template.get('name', f'Template {template_id}'),
        field_names=field_names,
        include_metadata=include_metadata
    )
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"extraction_results_{template.get('name', template_id)}_{timestamp}.xlsx"
    
    return send_file(
        excel_file,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )
