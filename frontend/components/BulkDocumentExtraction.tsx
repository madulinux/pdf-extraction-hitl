'use client';

import { useState } from 'react';
import { FileText, Loader2, Upload, X, CheckCircle2, AlertCircle } from 'lucide-react';
import { extractionAPI } from '@/lib/api/extraction.api';
import { Template } from '@/lib/types/template.types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';

interface BulkDocumentExtractionProps {
  selectedTemplate: Template | null;
  onExtractionComplete?: () => void;
}

export default function BulkDocumentExtraction({ 
  selectedTemplate, 
  onExtractionComplete 
}: BulkDocumentExtractionProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<{
    total: number;
    successful: number;
    failed: number;
    errors: Array<{ filename: string; error: string }>;
  } | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    const pdfFiles = selectedFiles.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length !== selectedFiles.length) {
      toast.error('Hanya file PDF yang diperbolehkan');
    }
    
    setFiles(pdfFiles);
    setResults(null);
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (files.length === 0 || !selectedTemplate) {
      toast.error('Harap pilih template dan minimal 1 file PDF');
      return;
    }

    setLoading(true);
    setProgress(0);
    setResults(null);

    try {
      toast.loading(`Mengekstraksi ${files.length} dokumen...`, { id: 'bulk-extraction' });
      
      // Simulate progress (since we don't have real-time progress from backend)
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 500);

      const result = await extractionAPI.extractBulk(files, selectedTemplate.id);
      
      clearInterval(progressInterval);
      setProgress(100);
      toast.dismiss('bulk-extraction');
      
      setResults({
        total: result.total,
        successful: result.successful,
        failed: result.failed,
        errors: result.errors,
      });

      if (result.failed === 0) {
        toast.success(
          `✅ Semua ${result.successful} dokumen berhasil diekstraksi!`,
          { duration: 5000 }
        );
      } else {
        toast.warning(
          `⚠️ ${result.successful} berhasil, ${result.failed} gagal`,
          { duration: 5000 }
        );
      }
      
      setFiles([]);
      const fileInput = document.getElementById('bulk-files') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
      if (onExtractionComplete) {
        onExtractionComplete();
      }
    } catch (err) {
      toast.dismiss('bulk-extraction');
      const errorMessage = err instanceof Error ? err.message : 'Gagal mengekstraksi dokumen';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="w-6 h-6" />
          Ekstraksi Bulk (Multiple Files)
        </CardTitle>
        <CardDescription>
          Upload beberapa dokumen PDF sekaligus untuk diekstraksi secara batch
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
              <p className="text-sm text-muted-foreground">
                {selectedTemplate.field_count} field akan diekstraksi per dokumen
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-lg hover:border-primary transition-colors">
                <div className="space-y-1 text-center">
                  <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
                  <div className="flex text-sm text-muted-foreground">
                    <label
                      htmlFor="bulk-files"
                      className="relative cursor-pointer rounded-md font-medium text-primary hover:text-primary/80 focus-within:outline-none"
                    >
                      <span>Upload multiple files</span>
                      <input
                        id="bulk-files"
                        type="file"
                        className="sr-only"
                        accept=".pdf"
                        multiple
                        onChange={handleFileChange}
                      />
                    </label>
                    <p className="pl-1">atau drag and drop</p>
                  </div>
                  <p className="text-xs text-muted-foreground">PDF files (multiple selection)</p>
                </div>
              </div>

              {files.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">{files.length} file terpilih:</p>
                  <div className="max-h-40 overflow-y-auto space-y-1">
                    {files.map((file, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-2 bg-muted rounded text-sm"
                      >
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <FileText className="w-4 h-4 flex-shrink-0" />
                          <span className="truncate">{file.name}</span>
                          <span className="text-muted-foreground text-xs flex-shrink-0">
                            ({(file.size / 1024).toFixed(1)} KB)
                          </span>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(index)}
                          disabled={loading}
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {loading && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Memproses dokumen...</span>
                  <span>{progress}%</span>
                </div>
                <Progress value={progress} />
              </div>
            )}

            {results && (
              <Alert variant={results.failed === 0 ? "default" : "destructive"}>
                <div className="flex items-start gap-2">
                  {results.failed === 0 ? (
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                  ) : (
                    <AlertCircle className="w-5 h-5" />
                  )}
                  <div className="flex-1">
                    <AlertDescription>
                      <div className="font-semibold mb-2">
                        Hasil Ekstraksi Bulk:
                      </div>
                      <ul className="space-y-1 text-sm">
                        <li>✅ Berhasil: {results.successful} dokumen</li>
                        <li>❌ Gagal: {results.failed} dokumen</li>
                        <li>📊 Total: {results.total} dokumen</li>
                      </ul>
                      {results.errors.length > 0 && (
                        <div className="mt-3">
                          <p className="font-semibold text-sm mb-1">Error Details:</p>
                          <ul className="space-y-1 text-xs">
                            {results.errors.map((error, idx) => (
                              <li key={idx} className="text-red-600">
                                • {error.filename}: {error.error}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </AlertDescription>
                  </div>
                </div>
              </Alert>
            )}

            <Button
              type="submit"
              disabled={loading || files.length === 0}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Mengekstraksi {files.length} Dokumen...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Ekstraksi {files.length} Dokumen
                </>
              )}
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
