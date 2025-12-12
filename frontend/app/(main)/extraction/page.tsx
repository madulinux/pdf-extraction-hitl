"use client";

import { useState } from "react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import TemplateList from "@/components/TemplateList";
import DocumentExtraction from "@/components/DocumentExtraction";
import BulkDocumentExtraction from "@/components/BulkDocumentExtraction";
import ExtractionList from "@/components/ExtractionList";
import { Template } from "@/lib/types/template.types";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileText, Upload } from "lucide-react";

function ExtractionPageContent() {
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(
    null
  );
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [activeTab, setActiveTab] = useState("single");

  const handleTemplateSelect = (template: Template) => {
    setSelectedTemplate(template);
  };

  const handleExtractionComplete = () => {
    // Trigger refresh of extraction list after successful extraction
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Ekstraksi Data</h1>
        <p className="text-muted-foreground">
          Upload dokumen PDF untuk diekstraksi dan validasi hasilnya
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column */}
        <div className="space-y-6">
          <TemplateList
            onSelectTemplate={handleTemplateSelect}
            refreshTrigger={0}
          />
          
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="single" className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Single File
              </TabsTrigger>
              <TabsTrigger value="bulk" className="flex items-center gap-2">
                <Upload className="w-4 h-4" />
                Bulk Upload
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="single" className="mt-4">
              <DocumentExtraction
                selectedTemplate={selectedTemplate}
                onExtractionComplete={handleExtractionComplete}
              />
            </TabsContent>
            
            <TabsContent value="bulk" className="mt-4">
              <BulkDocumentExtraction
                selectedTemplate={selectedTemplate}
                onExtractionComplete={handleExtractionComplete}
              />
            </TabsContent>
          </Tabs>
        </div>

        {/* Right Column */}
        <div>
          <ExtractionList
            key={refreshTrigger}
            templateId={selectedTemplate?.id}
          />
        </div>
      </div>
    </div>
  );
}

export default function ExtractionPage() {
  return (
    <ProtectedRoute>
      <ExtractionPageContent />
    </ProtectedRoute>
  );
}
