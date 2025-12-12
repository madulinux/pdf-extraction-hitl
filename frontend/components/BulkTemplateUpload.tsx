'use client';

import { useState } from 'react';
import { Upload, FileText, Loader2, X, CheckCircle2, AlertCircle } from 'lucide-react';
import { templatesAPI } from '@/lib/api/templates.api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';

interface BulkTemplateUploadProps {
  onSuccess?: () => void;
}

export default function BulkTemplateUpload({ onSuccess }: BulkTemplateUploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [namePrefix, setNamePrefix] = useState('');
  const [results, setResults] = useState<{
    total: number;
    successful: number;
    failed: number;
    errors: Array<{ filename: string; error: string }>;
  } | null>(null);

  const addFiles = (incomingFiles: File[]) => {
    const pdfFiles = incomingFiles.filter((file) => {
      const isPdfByType = file.type === 'application/pdf';
      const isPdfByName = file.name.toLowerCase().endsWith('.pdf');
      return isPdfByType || isPdfByName;
    });

    if (pdfFiles.length !== incomingFiles.length) {
      toast.error('Hanya file PDF yang diperbolehkan');
    }

    setFiles((prev) => {
      const seen = new Set(prev.map((f) => `${f.name}-${f.size}-${f.lastModified}`));
      const merged = [...prev];
      for (const f of pdfFiles) {
        const key = `${f.name}-${f.size}-${f.lastModified}`;
        if (!seen.has(key)) {
          merged.push(f);
          seen.add(key);
        }
      }
      return merged;
    });

    setResults(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    addFiles(selectedFiles);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!loading) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (loading) return;

    const droppedFiles = Array.from(e.dataTransfer.files || []);
    if (droppedFiles.length === 0) return;
    addFiles(droppedFiles);
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (files.length === 0) {
      toast.error('Harap pilih minimal 1 file PDF template');
      return;
    }

    setLoading(true);
    setProgress(0);
    setResults(null);

    try {
      toast.loading(`Menganalisis ${files.length} template...`, { id: 'bulk-template' });

      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 10, 90));
      }, 600);

      const result = await templatesAPI.createBulk(files, {
        nameMode: 'filename',
        namePrefix,
      });

      clearInterval(progressInterval);
      setProgress(100);
      toast.dismiss('bulk-template');

      setResults({
        total: result.total,
        successful: result.successful,
        failed: result.failed,
        errors: result.errors,
      });

      if (result.failed === 0) {
        toast.success(`✅ Semua ${result.successful} template berhasil dibuat!`, {
          duration: 5000,
        });
      } else {
        toast.warning(`⚠️ ${result.successful} berhasil, ${result.failed} gagal`, {
          duration: 5000,
        });
      }

      setFiles([]);
      const fileInput = document.getElementById('bulk-template-files') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

      if (onSuccess) onSuccess();
    } catch (err) {
      toast.dismiss('bulk-template');
      const errorMessage = err instanceof Error ? err.message : 'Gagal menganalisis template';
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
          Bulk Upload Template PDF
        </CardTitle>
        <CardDescription>
          Upload beberapa template PDF sekaligus untuk dianalisis dan dibuatkan konfigurasi field
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name-prefix">Prefix Nama Template (opsional)</Label>
            <Input
              id="name-prefix"
              value={namePrefix}
              onChange={(e) => setNamePrefix(e.target.value)}
              placeholder="Contoh: DatasetA_"
              disabled={loading}
            />
            <p className="text-xs text-muted-foreground">
              Nama template akan diambil dari nama file (tanpa .pdf), lalu ditambah prefix jika diisi.
            </p>
          </div>

          <div className="space-y-2">
            <div
              className={`flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-lg transition-colors ${
                isDragging ? 'border-primary bg-primary/5' : 'hover:border-primary'
              } ${loading ? 'opacity-60 pointer-events-none' : ''}`}
              onDragOver={handleDragOver}
              onDragEnter={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="space-y-1 text-center">
                <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
                <div className="flex text-sm text-muted-foreground">
                  <label
                    htmlFor="bulk-template-files"
                    className="relative cursor-pointer rounded-md font-medium text-primary hover:text-primary/80 focus-within:outline-none"
                  >
                    <span>Upload multiple files</span>
                    <input
                      id="bulk-template-files"
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
                <span>Menganalisis template...</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} />
            </div>
          )}

          {results && (
            <Alert variant={results.failed === 0 ? 'default' : 'destructive'}>
              <div className="flex items-start gap-2">
                {results.failed === 0 ? (
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                ) : (
                  <AlertCircle className="w-5 h-5" />
                )}
                <div className="flex-1">
                  <AlertDescription>
                    <div className="font-semibold mb-2">Hasil Bulk Upload Template:</div>
                    <ul className="space-y-1 text-sm">
                      <li>✅ Berhasil: {results.successful} template</li>
                      <li>❌ Gagal: {results.failed} template</li>
                      <li>📊 Total: {results.total} template</li>
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

          <Button type="submit" disabled={loading || files.length === 0} className="w-full">
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Menganalisis {files.length} Template...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4 mr-2" />
                Analisis {files.length} Template
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
