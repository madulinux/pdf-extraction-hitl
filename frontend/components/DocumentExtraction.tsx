'use client';

import { useState } from 'react';
import { FileText, Loader2, Brain, AlertTriangle } from 'lucide-react';
import { extractionAPI } from '@/lib/api/extraction.api';
import { checkValidationNeeded } from '@/lib/api/learning.api';
import { Template } from '@/lib/types/template.types';
import { ExtractionResult } from '@/lib/types/extraction.types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import FileUpload from './shared/FileUpload';

interface DocumentExtractionProps {
  selectedTemplate: Template | null;
  onExtractionComplete?: (documentId: number, results: ExtractionResult) => void;
}

export default function DocumentExtraction({ selectedTemplate, onExtractionComplete }: DocumentExtractionProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleFileChange = (file: File | null) => {
    setFile(file);
    setError('');
    // const selectedFile = e.target.files?.[0];
    // if (selectedFile && selectedFile.type === 'application/pdf') {
    //   setFile(selectedFile);
    //   setError('');
    // } else {
    //   setError('Harap pilih file PDF');
    // }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file || !selectedTemplate) {
      setError('Harap pilih template dan file PDF');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Step 1: Extract data
      toast.loading('Mengekstraksi data dari PDF...', { id: 'extraction' });
      const result = await extractionAPI.extract(file, selectedTemplate.id);
      toast.dismiss('extraction');
      
      // Step 2: Active Learning - Check if validation needed
      toast.loading('Menganalisis confidence...', { id: 'validation-check' });
      
      try {
        const validationCheck = await checkValidationNeeded(result.results as unknown as Record<string, unknown>);
        toast.dismiss('validation-check');
        
        if (validationCheck.should_validate) {
          // Low confidence - needs validation
          toast.warning(
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                <span className="font-semibold">Validasi Diperlukan</span>
              </div>
              <span className="text-sm">{validationCheck.reason}</span>
            </div>,
            { duration: 5000 }
          );
          setSuccess('Data berhasil diekstraksi! Silakan validasi hasil ekstraksi.');
        } else {
          // High confidence - auto-accept
          toast.success(
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <Brain className="h-4 w-4" />
                <span className="font-semibold">High Confidence!</span>
              </div>
              <span className="text-sm">{validationCheck.reason}</span>
              <span className="text-xs text-muted-foreground">
                Sistem yakin dengan hasil ekstraksi
              </span>
            </div>,
            { duration: 5000 }
          );
          setSuccess('✅ Data berhasil diekstraksi dengan confidence tinggi!');
        }
      } catch (validationError) {
        // If validation check fails, still show success
        console.warn('Validation check failed:', validationError);
        toast.success('Data berhasil diekstraksi!');
        setSuccess('Data berhasil diekstraksi! Silakan validasi hasil ekstraksi.');
      }
      
      setFile(null);
      
      // Reset file input
      const fileInput = document.getElementById('document-file') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
      if (onExtractionComplete) {
        onExtractionComplete(result.document_id, result.results);
      }
    } catch (err) {
      toast.dismiss('extraction');
      toast.dismiss('validation-check');
      const errorMessage = err instanceof Error ? err.message : 'Gagal mengekstraksi dokumen';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="w-6 h-6" />
          Ekstraksi Dokumen
        </CardTitle>
        <CardDescription>
          Upload dokumen PDF yang sudah diisi untuk diekstraksi datanya
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!selectedTemplate ? (
          <Alert>
            <AlertDescription>
              Silakan pilih template terlebih dahulu dari daftar template di atas.
            </AlertDescription>
          </Alert>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm font-medium">Template Terpilih:</p>
              <p className="text-lg font-semibold text-primary">{selectedTemplate.name}</p>
              <p className="text-sm text-muted-foreground">{selectedTemplate.field_count} field akan diekstraksi</p>
            </div>

            <div className="space-y-2">
              {/* <Label htmlFor="document-file">File PDF Dokumen</Label>
              <div className="flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-lg hover:border-primary transition-colors">
                <div className="space-y-1 text-center">
                  <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
                  <div className="flex text-sm text-muted-foreground">
                    <label
                      htmlFor="document-file"
                      className="relative cursor-pointer rounded-md font-medium text-primary hover:text-primary/80 focus-within:outline-none"
                    >
                      <span>Upload file</span>
                      <input
                        id="document-file"
                        type="file"
                        className="sr-only"
                        accept=".pdf"
                        onChange={handleFileChange}
                        required
                      />
                    </label>
                    <p className="pl-1">atau drag and drop</p>
                  </div>
                  <p className="text-xs text-muted-foreground">PDF hingga 16MB</p>
                  {file && (
                    <p className="text-sm text-green-600 font-medium mt-2 flex items-center justify-center gap-1">
                      <CheckCircle2 className="w-4 h-4" />
                      {file.name}
                    </p>
                  )}
                </div>
              </div> */}
              <FileUpload
                accept=".pdf"
                label="File PDF Dokumen"
                name="document-file"
                onChange={(file) => {
                  if (file) {
                    handleFileChange(file);
                  }
                }}
                required
                value={file}
              />
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert>
                <AlertDescription>{success}</AlertDescription>
              </Alert>
            )}

            <Button
              type="submit"
              disabled={loading || !file}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Mengekstraksi Data...
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4 mr-2" />
                  Ekstraksi Data
                </>
              )}
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
