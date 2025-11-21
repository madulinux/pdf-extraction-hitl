'use client';

import { useState } from 'react';
import { Upload, FileText, Loader2 } from 'lucide-react';
import { templatesAPI } from '@/lib/api/templates.api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import FileUpload from './shared/FileUpload';

interface TemplateUploadProps {
  onSuccess?: () => void;
}

export default function TemplateUpload({ onSuccess }: TemplateUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [templateName, setTemplateName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleFileChange = (file: File | null) => {
    setFile(file);
    setError('');
    if (!templateName) {
      setTemplateName(file?.name.replace('.pdf', '') || '');
    }

    // const selectedFile = e.target.files?.[0];
    // if (selectedFile && selectedFile.type === 'application/pdf') {
    //   setFile(selectedFile);
    //   setError('');
    //   // Auto-fill template name from filename
    //   if (!templateName) {
    //     setTemplateName(selectedFile.name.replace('.pdf', ''));
    //   }
    // } else {
    //   setError('Harap pilih file PDF');
    // }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file || !templateName) {
      setError('Harap lengkapi semua field');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const result = await templatesAPI.create(file, templateName);
      setSuccess(`Template berhasil dibuat!`);
      setFile(null);
      setTemplateName('');
      
      // Reset file input
      const fileInput = document.getElementById('template-file') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
      if (onSuccess) onSuccess();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Gagal menganalisis template';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="w-6 h-6" />
          Upload Template PDF
        </CardTitle>
        <CardDescription>
          Upload template PDF untuk dianalisis dan mengidentifikasi field yang dapat diekstraksi
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="template-name">Nama Template</Label>
            <Input
              type="text"
              id="template-name"
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              placeholder="Contoh: Formulir Pendaftaran"
              required
            />
          </div>

          <div className="space-y-2">
            {/* <div className="flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-lg hover:border-primary transition-colors">
              <div className="space-y-1 text-center">
                <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
                <div className="flex text-sm text-muted-foreground">
                  <label
                    htmlFor="template-file"
                    className="relative cursor-pointer rounded-md font-medium text-primary hover:text-primary/80 focus-within:outline-none"
                  >
                    <span>Upload file</span>
                    <Input
                      id="template-file"
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
                  <p className="text-sm text-green-600 font-medium mt-2">
                    ✓ {file.name}
                  </p>
                )}
              </div>
            </div> */}
            <FileUpload
              accept=".pdf"
              label="File PDF Template"
              name="template-file"
              onChange={(file) => {
                if (file) {
                  handleFileChange(file);
                }
              }}
              value={file}
              required
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
            disabled={loading || !file || !templateName}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Menganalisis...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4 mr-2" />
                Analisis Template
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
