'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, FileText, Calendar, Hash } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import TemplatePreview from '@/components/TemplatePreview';
import { templatesAPI } from '@/lib/api/templates.api';
import { Template } from '@/lib/types/template.types';

export default function TemplateDetailPage() {
  const params = useParams();
  const router = useRouter();
  const templateId = parseInt(params.id as string);
  
  const [template, setTemplate] = useState<Template | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadTemplate();
  }, [templateId]);

  const loadTemplate = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await templatesAPI.getById(templateId);
      setTemplate(data.template);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Gagal memuat template';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <Skeleton className="h-8 w-64" />
        </div>
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error || !template) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.push('/templates')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Kembali
        </Button>
        <Alert variant="destructive">
          <AlertDescription>{error || 'Template tidak ditemukan'}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push('/templates')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{template.name}</h1>
            <p className="text-muted-foreground">Detail template dan field yang terdeteksi</p>
          </div>
        </div>
        <Badge variant="secondary" className="text-sm">
          {template.status}
        </Badge>
      </div>

      {/* Template Info */}
      <Card>
        <CardHeader>
          <CardTitle>Informasi Template</CardTitle>
          <CardDescription>Metadata dan statistik template</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <FileText className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Nama File</p>
                <p className="font-medium">{template.filename}</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Hash className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Jumlah Field</p>
                <p className="font-medium">{template.field_count} field</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Calendar className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Dibuat</p>
                <p className="font-medium">
                  {new Date(template.created_at).toLocaleDateString('id-ID', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Template Preview with Fields */}
      <TemplatePreview templateId={templateId} />
    </div>
  );
}
