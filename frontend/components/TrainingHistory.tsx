"use client";

import { useState, useEffect } from "react";
import { History, Calendar, TrendingUp, Database } from "lucide-react";
import { learningAPI } from "@/lib/api/learning.api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface TrainingRecord {
  id: number;
  template_id: number;
  model_path: string;
  training_samples: number;
  accuracy: number;
  precision_score: number;
  recall_score: number;
  f1_score: number;
  trained_at: string;
}

interface TrainingHistoryProps {
  templateId: number;
  templateName: string;
}

export default function TrainingHistory({
  templateId,
  templateName,
}: TrainingHistoryProps) {
  const [open, setOpen] = useState(false);
  const [history, setHistory] = useState<TrainingRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadHistory = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await learningAPI.getHistory(templateId);
      setHistory(result.history || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat riwayat");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) {
      loadHistory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, templateId]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("id-ID", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatPercentage = (value: number | null) => {
    if (value === null || value === undefined) return "N/A";
    return `${(value * 100).toFixed(2)}%`;
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <History className="w-4 h-4 mr-2" />
          Riwayat Pelatihan
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <History className="w-5 h-5" />
            Riwayat Pelatihan Model
          </DialogTitle>
          <DialogDescription>
            Semua riwayat pelatihan untuk template: <strong>{templateName}</strong>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : history.length === 0 ? (
            <Alert>
              <AlertDescription>
                Belum ada riwayat pelatihan untuk template ini.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50px]">#</TableHead>
                    <TableHead>
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        Tanggal
                      </div>
                    </TableHead>
                    <TableHead>
                      <div className="flex items-center gap-1">
                        <Database className="w-4 h-4" />
                        Samples
                      </div>
                    </TableHead>
                    <TableHead>
                      <div className="flex items-center gap-1">
                        <TrendingUp className="w-4 h-4" />
                        Accuracy
                      </div>
                    </TableHead>
                    <TableHead>Precision</TableHead>
                    <TableHead>Recall</TableHead>
                    <TableHead>F1 Score</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {history.map((record, index) => (
                    <TableRow key={record.id}>
                      <TableCell className="font-medium">
                        {history.length - index}
                      </TableCell>
                      <TableCell className="text-sm">
                        {formatDate(record.trained_at)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          {record.training_samples}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            record.accuracy && record.accuracy >= 0.9
                              ? "default"
                              : "secondary"
                          }
                        >
                          {formatPercentage(record.accuracy)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {formatPercentage(record.precision_score)}
                      </TableCell>
                      <TableCell>
                        {formatPercentage(record.recall_score)}
                      </TableCell>
                      <TableCell>
                        {formatPercentage(record.f1_score)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          {history.length > 0 && (
            <div className="text-sm text-muted-foreground text-center">
              Total {history.length} riwayat pelatihan
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
