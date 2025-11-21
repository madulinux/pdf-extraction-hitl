'use client';

import { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import TemplateList from '@/components/TemplateList';
import ModelTraining from '@/components/ModelTraining';
import { Template } from '@/lib/types/template.types';

function TrainingPageContent() {
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);

  const handleTemplateSelect = (template: Template) => {
    setSelectedTemplate(template);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Pelatihan Model</h1>
        <p className="text-muted-foreground">
          Latih model CRF dengan feedback dari validasi pengguna
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <TemplateList
            onSelectTemplate={handleTemplateSelect}
            refreshTrigger={0}
          />
        </div>
        <div className="lg:col-span-2">
          <ModelTraining selectedTemplate={selectedTemplate} />
        </div>
      </div>
    </div>
  );
}

export default function TrainingPage() {
  return (
    <ProtectedRoute>
      <TrainingPageContent />
    </ProtectedRoute>
  );
}
