'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { extractionAPI } from '@/lib/api/extraction.api';
import { Document, ExtractionResult } from '@/lib/types/extraction.types';
import { ArrowLeft, FileText } from 'lucide-react';
import ValidationForm from '@/components/ValidationForm';

function ValidationPageContent() {
  const params = useParams();
  const router = useRouter();
  const RAW_API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const API_BASE_URL = RAW_API_BASE_URL.replace(/\/+$/, '').endsWith('/api')
    ? RAW_API_BASE_URL.replace(/\/+$/, '')
    : `${RAW_API_BASE_URL.replace(/\/+$/, '')}/api`;

  const documentId = parseInt(params.id as string);

  const [document, setDocument] = useState<Document | null>(null);
  const [extractionResults, setExtractionResults] = useState<ExtractionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadDocument = async () => {
    try {
      setLoading(true);
      const response = await extractionAPI.getById(documentId);
      setDocument(response.document);
      
      // Parse extraction results
      if (response.document.extraction_result) {
        const results = typeof response.document.extraction_result === 'string'
          ? JSON.parse(response.document.extraction_result)
          : response.document.extraction_result;
        
        // Set the full extraction result object (not just extracted_data)
        setExtractionResults(results);
      }
    } catch (err) {
      setError('Gagal memuat dokumen');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocument();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId]);

  const handleValidationComplete = () => {
    router.push('/extraction');
  };

  const handleBack = () => {
    router.push('/extraction');
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'extracted':
        return <Badge variant="default" className="bg-blue-500">Perlu Validasi</Badge>;
      case 'validated':
        return <Badge variant="default" className="bg-green-500">Tervalidasi</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={handleBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Kembali
        </Button>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-red-500">
              {error || 'Dokumen tidak ditemukan'}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Kembali
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Validasi & Koreksi</h1>
            <p className="text-muted-foreground">
              Periksa dan koreksi hasil ekstraksi data
            </p>
          </div>
        </div>
        {getStatusBadge(document.status)}
      </div>

      {/* Document Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5 text-muted-foreground" />
            <div>
              <CardTitle>{document.filename}</CardTitle>
              <CardDescription>
                Template ID: {document.template_id} • 
                Diekstraksi: {new Date(document.created_at).toLocaleString('id-ID')}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Main Content: PDF Preview + Validation Form */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: PDF Preview */}
        <Card className="lg:sticky lg:top-6 h-fit">
          <CardHeader>
            <CardTitle>Preview Dokumen</CardTitle>
            <CardDescription>
              Dokumen PDF yang diekstraksi
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg overflow-hidden bg-gray-50">
              {/* PDF Preview - Using iframe */}
              <div className="aspect-[8.5/11] relative">
                <iframe
                  src={`${API_BASE_URL}/v1/extraction/documents/${documentId}/preview?token=${localStorage.getItem('access_token')}`}
                  className="w-full h-full border-0"
                  title="PDF Preview"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Right: Validation Form with Integrated History */}
        <div className="space-y-6">
          <ValidationForm
            documentId={documentId}
            extractionResults={extractionResults}
            feedbackHistory={document.feedback_history || []}
            onValidationComplete={handleValidationComplete}
          />
        </div>
      </div>
    </div>
  );
}

export default function ValidationPage() {
  return (
    <ProtectedRoute>
      <ValidationPageContent />
    </ProtectedRoute>
  );
}
