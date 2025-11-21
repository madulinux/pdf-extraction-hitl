'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText, Database, Brain, TrendingUp } from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function HomeContent() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Selamat datang di Sistem Ekstraksi Data Adaptif PDF dengan Human-in-the-Loop
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Template</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">-</div>
            <p className="text-xs text-muted-foreground">Template PDF tersedia</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Dokumen Diekstraksi</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">-</div>
            <p className="text-xs text-muted-foreground">Total dokumen diproses</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Feedback Tersedia</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">-</div>
            <p className="text-xs text-muted-foreground">Siap untuk pelatihan</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Model Terlatih</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">-</div>
            <p className="text-xs text-muted-foreground">Model CRF aktif</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Tentang Sistem</CardTitle>
            <CardDescription>
              Sistem Ekstraksi Data Adaptif dari Template PDF berbasis Human-in-the-Loop
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2">Fitur Utama:</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                <li>Analisis Template PDF untuk identifikasi field otomatis</li>
                <li>Ekstraksi Data Hybrid (Rule-based + Machine Learning CRF)</li>
                <li>Validasi & Koreksi dengan Human-in-the-Loop</li>
                <li>Pembelajaran Adaptif dari feedback pengguna</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Cara Penggunaan:</h3>
              <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground">
                <li>Upload template PDF di menu &apos;Kelola Template&apos;</li>
                <li>Ekstraksi dokumen yang sudah diisi di menu &apos;Ekstraksi Data&apos;</li>
                <li>Validasi dan koreksi hasil ekstraksi</li>
                <li>Latih model dengan feedback di menu &apos;Pelatihan Model&apos;</li>
              </ol>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Teknologi</CardTitle>
            <CardDescription>Stack yang digunakan</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <h4 className="font-semibold text-sm mb-1">Backend</h4>
              <p className="text-xs text-muted-foreground">
                Python 3.12, Flask, pdfplumber, sklearn-crfsuite, SQLite
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-sm mb-1">Frontend</h4>
              <p className="text-xs text-muted-foreground">
                Next.js 16, TypeScript, Tailwind CSS, shadcn/ui
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-sm mb-1">Machine Learning</h4>
              <p className="text-xs text-muted-foreground">
                Conditional Random Fields (CRF) dengan BIO tagging
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <ProtectedRoute>
      <HomeContent />
    </ProtectedRoute>
  );
}
