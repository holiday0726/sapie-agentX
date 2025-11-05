import { useState } from "react";
import ForwardedIconComponent from "@/components/common/genericIconComponent";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  SidebarGroup,
  SidebarGroupContent,
} from "@/components/ui/sidebar";
import { cn } from "@/utils/utils";

const EXAMPLE_PROMPTS = [
  "Create a simple chatbot with memory",
  "Build a document Q&A system",
  "Make a sentiment analysis flow",
  "Create a text summarization pipeline",
];

export default function NlToFlowPanel() {
  const [prompt, setPrompt] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  const handleExampleClick = (example: string) => {
    setPrompt(example);
  };

  const handleGenerate = () => {
    if (!prompt.trim()) return;
    
    // TODO: Implement actual generation logic
    setIsGenerating(true);
    
    // Simulate generation
    setTimeout(() => {
      setIsGenerating(false);
    }, 2000);
  };

  return (
    <div className="flex flex-col h-full">
      <SidebarGroup>
        <SidebarGroupContent>
          <div className="flex flex-col gap-4 px-3 py-4">
            {/* Title and Description */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <ForwardedIconComponent name="sparkles" className="h-4 w-4" />
                <span>AI Flow Builder</span>
              </div>
              <div className="text-xs text-muted-foreground">
                자연어로 원하는 플로우를 설명하면 자동으로 생성해드립니다.
              </div>
            </div>

            {/* Input Area */}
            <div className="flex flex-col gap-2">
              <label className="text-xs font-medium">
                플로우 설명
              </label>
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="예: '사용자 질문에 답변하는 챗봇을 만들어주세요...'"
                className="min-h-[120px] resize-none text-sm"
                disabled={isGenerating}
              />
            </div>

            {/* Generate Button */}
            <Button
              onClick={handleGenerate}
              disabled={!prompt.trim() || isGenerating}
              className="w-full"
            >
              {isGenerating ? (
                <>
                  <ForwardedIconComponent
                    name="loader-circle"
                    className="h-4 w-4 mr-2 animate-spin"
                  />
                  생성 중...
                </>
              ) : (
                <>
                  <ForwardedIconComponent
                    name="sparkles"
                    className="h-4 w-4 mr-2"
                  />
                  플로우 생성
                </>
              )}
            </Button>
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    </div>
  );
}

