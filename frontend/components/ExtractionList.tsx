"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { extractionAPI } from "@/lib/api/extraction.api";
import { Document } from "@/lib/types/extraction.types";
import {
  FileText,
  CheckCircle,
  Clock,
  AlertCircle,
  EyeIcon,
} from "lucide-react";
import { Input } from "./ui/input";
import SimplePagination from "./ui/simple-pagination";

export default function ExtractionList({
  templateId,
}: {
  templateId?: number;
}) {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  useEffect(() => {
    loadDocuments();
  }, [search, templateId, page, pageSize]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const response = await extractionAPI.listDocuments({
        search,
        templateId,
        page,
        pageSize,
      });
      setDocuments(response.documents);
      setPage(Number(response.meta.page));
      setTotalPages(Number(response.meta.total_pages));
    } catch (err) {
      setError("Gagal memuat daftar dokumen");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleValidate = (documentId: number) => {
    router.push(`/extraction/validate/${documentId}`);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "extracted":
        return (
          <Badge variant="default" className="bg-blue-500">
            <Clock className="w-3 h-3 mr-1" />
            Perlu Validasi
          </Badge>
        );
      case "validated":
        return (
          <Badge variant="default" className="bg-green-500">
            <CheckCircle className="w-3 h-3 mr-1" />
            Tervalidasi
          </Badge>
        );
      case "pending":
        return (
          <Badge variant="secondary">
            <AlertCircle className="w-3 h-3 mr-1" />
            Pending
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("id-ID", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Daftar Hasil Ekstraksi</CardTitle>
          <CardDescription>Memuat data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Daftar Hasil Ekstraksi</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-red-500">{error}</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Daftar Hasil Ekstraksi</CardTitle>
        <CardDescription>
          {documents.length} dokumen telah diekstraksi
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between mb-4">
          <Input
            type="text"
            placeholder="Cari dokumen..."
            value={search}
            className="w-1/2"
            autoFocus
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {totalPages > 1 && (
          <div className="p-4">
            <SimplePagination
              page={page}
              totalPages={totalPages}
              pageSize={pageSize}
              onPageChange={(newPage) => setPage(newPage)}
              onPageSizeChange={(newPageSize) => setPageSize(newPageSize)}
            />
          </div>
        )}
        {documents.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Belum ada dokumen yang diekstraksi</p>
            <p className="text-sm mt-2">
              Upload dokumen untuk memulai ekstraksi
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors gap-4"
              >
                <div className="flex items-start gap-3 flex-1">
                  <FileText className="w-5 h-5 mt-1 text-muted-foreground" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-medium truncate">
                        {doc.filename.length > 40
                          ? `${doc.filename.substring(0, 40)}...`
                          : doc.filename}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 justify-between">
                      <p className="text-sm text-muted-foreground">
                        {doc.template_name} • {formatDate(doc.created_at)}
                      </p>
                      {getStatusBadge(doc.status)}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  {doc.status === "extracted" && (
                    <Button
                      size="icon"
                      variant="secondary"
                      onClick={() => handleValidate(doc.id)}
                    >
                      <CheckCircle className="w-4 h-4" />
                    </Button>
                  )}
                  {doc.status === "validated" && (
                    <Button
                      size="icon"
                      variant="default"
                      onClick={() => handleValidate(doc.id)}
                    >
                      <EyeIcon className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        {totalPages > 1 && (
          <div className="p-4">
            <SimplePagination
              page={page}
              totalPages={totalPages}
              pageSize={pageSize}
              onPageChange={(newPage) => setPage(newPage)}
              onPageSizeChange={(newPageSize) => setPageSize(newPageSize)}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
