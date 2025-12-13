/**
 * 전략 템플릿 관리자 컴포넌트
 * 
 * 템플릿 저장, 불러오기, 삭제 기능 제공
 */

'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Save, FolderOpen, Trash2, Download, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { StrategyDraft } from '@/types/strategy-draft';
import {
  getTemplates,
  saveTemplate,
  loadTemplate,
  deleteTemplate,
  exportTemplate,
  importTemplate,
  type StrategyTemplate
} from '@/lib/template-storage';
import { formatDate } from '@/lib/utils';

interface TemplateManagerProps {
  draft: StrategyDraft;
  onLoadTemplate: (draft: StrategyDraft) => void;
}

/**
 * 템플릿 관리자
 */
export function TemplateManager({ draft, onLoadTemplate }: TemplateManagerProps) {
  const [templates, setTemplates] = useState<StrategyTemplate[]>([]);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [showLoadDialog, setShowLoadDialog] = useState(false);
  
  // 저장 폼 상태
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');
  
  // 템플릿 목록 로드
  useEffect(() => {
    loadTemplateList();
  }, []);
  
  // 템플릿 목록 새로고침
  const loadTemplateList = () => {
    setTemplates(getTemplates());
  };
  
  // 템플릿 저장 핸들러
  const handleSave = () => {
    if (!templateName.trim()) {
      toast.error('템플릿 이름을 입력해주세요');
      return;
    }
    
    try {
      const newTemplate = saveTemplate(templateName, templateDescription, draft);
      toast.success('템플릿이 저장되었습니다', {
        description: newTemplate.name
      });
      
      // 폼 초기화
      setTemplateName('');
      setTemplateDescription('');
      setShowSaveDialog(false);
      
      // 목록 새로고침
      loadTemplateList();
    } catch (error: any) {
      toast.error('템플릿 저장에 실패했습니다', {
        description: error.message
      });
    }
  };
  
  // 템플릿 불러오기 핸들러
  const handleLoad = (template: StrategyTemplate) => {
    try {
      onLoadTemplate(template.draft);
      toast.success('템플릿을 불러왔습니다', {
        description: template.name
      });
      setShowLoadDialog(false);
    } catch (error: any) {
      toast.error('템플릿 불러오기에 실패했습니다', {
        description: error.message
      });
    }
  };
  
  // 템플릿 삭제 핸들러
  const handleDelete = (id: string, name: string) => {
    try {
      const success = deleteTemplate(id);
      if (success) {
        toast.success('템플릿이 삭제되었습니다', {
          description: name
        });
        loadTemplateList();
      } else {
        toast.error('템플릿 삭제에 실패했습니다');
      }
    } catch (error: any) {
      toast.error('템플릿 삭제에 실패했습니다', {
        description: error.message
      });
    }
  };
  
  // 템플릿 내보내기 핸들러
  const handleExport = (template: StrategyTemplate) => {
    try {
      exportTemplate(template);
      toast.success('템플릿을 다운로드했습니다', {
        description: template.name
      });
    } catch (error: any) {
      toast.error('템플릿 내보내기에 실패했습니다', {
        description: error.message
      });
    }
  };
  
  // 템플릿 가져오기 핸들러
  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    
    input.onchange = async (e: any) => {
      const file = e.target.files[0];
      if (!file) return;
      
      try {
        const text = await file.text();
        const template = importTemplate(text);
        toast.success('템플릿을 가져왔습니다', {
          description: template.name
        });
        loadTemplateList();
      } catch (error: any) {
        toast.error('템플릿 가져오기에 실패했습니다', {
          description: error.message
        });
      }
    };
    
    input.click();
  };
  
  return (
    <div className="flex gap-2">
      {/* 저장 버튼 */}
      <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <DialogTrigger asChild>
          <Button variant="outline" size="sm">
            <Save className="mr-2 h-4 w-4" />
            템플릿 저장
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>템플릿으로 저장</DialogTitle>
            <DialogDescription>
              현재 전략을 템플릿으로 저장하여 나중에 다시 사용할 수 있습니다.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="template-name">템플릿 이름</Label>
              <Input
                id="template-name"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                placeholder="예: EMA Cross 기본 설정"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="template-description">설명 (선택)</Label>
              <Input
                id="template-description"
                value={templateDescription}
                onChange={(e) => setTemplateDescription(e.target.value)}
                placeholder="템플릿에 대한 설명"
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSaveDialog(false)}>
              취소
            </Button>
            <Button onClick={handleSave}>저장</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* 불러오기 버튼 */}
      <Dialog open={showLoadDialog} onOpenChange={setShowLoadDialog}>
        <DialogTrigger asChild>
          <Button variant="outline" size="sm">
            <FolderOpen className="mr-2 h-4 w-4" />
            템플릿 불러오기
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>템플릿 불러오기</DialogTitle>
            <DialogDescription>
              저장된 템플릿을 선택하여 전략을 불러옵니다.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4 max-h-[400px] overflow-y-auto">
            {templates.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                저장된 템플릿이 없습니다
              </div>
            ) : (
              templates.map((template) => (
                <Card key={template.id}>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">{template.name}</CardTitle>
                    <CardDescription className="text-sm">
                      {template.description || '설명 없음'}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">
                        생성일: {formatDate(template.createdAt)}
                      </span>
                      <div className="flex gap-1">
                        <Button
                          size="sm"
                          variant="default"
                          onClick={() => handleLoad(template)}
                        >
                          불러오기
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleExport(template)}
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button size="sm" variant="ghost">
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>템플릿 삭제</AlertDialogTitle>
                              <AlertDialogDescription>
                                &ldquo;{template.name}&rdquo; 템플릿을 삭제하시겠습니까?
                                이 작업은 되돌릴 수 없습니다.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>취소</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleDelete(template.id, template.name)}
                              >
                                삭제
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={handleImport}>
              <Upload className="mr-2 h-4 w-4" />
              파일에서 가져오기
            </Button>
            <Button variant="outline" onClick={() => setShowLoadDialog(false)}>
              닫기
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

