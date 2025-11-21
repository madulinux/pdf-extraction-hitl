'use client';

import { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import TemplateUpload from '@/components/TemplateUpload';
import TemplateList from '@/components/TemplateList';
import { Template } from '@/lib/types/template.types';

function TemplatesPageContent() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);

  const handleTemplateUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const handleTemplateSelect = (template: Template) => {
    setSelectedTemplate(template);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Kelola Template</h1>
        <p className="text-muted-foreground">
          Upload dan kelola template PDF untuk ekstraksi data
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TemplateUpload onSuccess={handleTemplateUploadSuccess} />
        <TemplateList
          onSelectTemplate={handleTemplateSelect}
          refreshTrigger={refreshTrigger}
          showDetailButton={true}
        />
      </div>

      {selectedTemplate && (
        <div className="mt-6 p-6 border rounded-lg bg-muted/50">
          <h3 className="font-semibold text-lg mb-4">Detail Template</h3>
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="font-medium text-muted-foreground">Nama Template:</dt>
              <dd className="mt-1">{selectedTemplate.name}</dd>
            </div>
            <div>
              <dt className="font-medium text-muted-foreground">Filename:</dt>
              <dd className="mt-1">{selectedTemplate.filename}</dd>
            </div>
            <div>
              <dt className="font-medium text-muted-foreground">Jumlah Field:</dt>
              <dd className="mt-1">{selectedTemplate.field_count} field</dd>
            </div>
            <div>
              <dt className="font-medium text-muted-foreground">Dibuat:</dt>
              <dd className="mt-1">
                {new Date(selectedTemplate.created_at).toLocaleDateString('id-ID')}
              </dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  );
}

export default function TemplatesPage() {
  return (
    <ProtectedRoute>
      <TemplatesPageContent />
    </ProtectedRoute>
  );
}
