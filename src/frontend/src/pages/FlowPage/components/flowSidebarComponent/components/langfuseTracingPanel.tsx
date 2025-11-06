import { useState } from "react";
import ForwardedIconComponent from "@/components/common/genericIconComponent";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  SidebarGroup,
  SidebarGroupContent,
} from "@/components/ui/sidebar";
import { useGetLangfuseStatus } from "@/controllers/API/queries/langfuse/use-get-langfuse-status";
import { useGetLangfuseTraces } from "@/controllers/API/queries/langfuse/use-get-langfuse-traces";
import { useGetLangfuseTraceDetail } from "@/controllers/API/queries/langfuse/use-get-langfuse-trace-detail";

export default function LangfuseTracingPanel() {
  const [limit] = useState(10);
  const [offset] = useState(0);
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);

  // Fetch connection status
  const { data: statusData, isLoading: statusLoading } =
    useGetLangfuseStatus();

  // Fetch traces only if connected
  const {
    data: tracesData,
    isLoading: tracesLoading,
    refetch: refetchTraces,
  } = useGetLangfuseTraces({
    limit,
    offset,
    enabled: statusData?.connected === true,
  });

  // Fetch trace detail when a trace is selected
  const { data: traceDetail, isLoading: traceDetailLoading } =
    useGetLangfuseTraceDetail({
      traceId: selectedTraceId || "",
      enabled: !!selectedTraceId,
    });

  const isConnected = statusData?.connected === true;
  const traces = tracesData?.traces || [];

  const handleTraceClick = (traceId: string) => {
    setSelectedTraceId(traceId);
  };

  const handleCloseModal = () => {
    setSelectedTraceId(null);
  };

  const formatCost = (cost: number | null) => {
    if (cost === null || cost === undefined) return "N/A";
    return `$${cost.toFixed(4)}`;
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

      if (seconds < 60) {
        return `${seconds}초 전`;
      }
      const minutes = Math.floor(seconds / 60);
      if (minutes < 60) {
        return `${minutes}분 전`;
      }
      const hours = Math.floor(minutes / 60);
      if (hours < 24) {
        return `${hours}시간 전`;
      }
      const days = Math.floor(hours / 24);
      if (days < 30) {
        return `${days}일 전`;
      }
      const months = Math.floor(days / 30);
      if (months < 12) {
        return `${months}개월 전`;
      }
      const years = Math.floor(months / 12);
      return `${years}년 전`;
    } catch {
      return timestamp;
    }
  };

  const handleRefresh = () => {
    refetchTraces();
  };

  return (
    <div className="flex flex-col h-full">
      <SidebarGroup>
        <SidebarGroupContent>
          <div className="flex flex-col gap-4 px-3 pb-4">
            {/* Title and Status */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <ForwardedIconComponent name="activity" className="h-4 w-4" />
                <span>Langfuse 트레이싱</span>
              </div>
              
              <Badge
                variant={isConnected ? "default" : "destructive"}
                className="text-xs w-fit"
              >
                {statusLoading
                  ? "확인 중..."
                  : isConnected
                    ? "연결됨"
                    : "연결 안됨"}
              </Badge>

              {statusData?.error && (
                <div className="text-xs text-destructive">
                  오류: {statusData.error}
                </div>
              )}
            </div>

            {/* Connection Instructions */}
            {!isConnected && !statusLoading && (
              <div className="bg-muted p-3 rounded-md text-xs text-muted-foreground">
                <p className="font-medium mb-2">연결 설정이 필요합니다:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>LANGFUSE_SECRET_KEY</li>
                  <li>LANGFUSE_PUBLIC_KEY</li>
                  <li>LANGFUSE_HOST</li>
                </ul>
                <p className="mt-2">
                  환경 변수를 설정하고 서버를 재시작하세요.
                </p>
              </div>
            )}

            {/* Refresh Button */}
            {isConnected && (
              <Button
                onClick={handleRefresh}
                disabled={tracesLoading}
                variant="outline"
                size="sm"
                className="w-full"
              >
                {tracesLoading ? (
                  <>
                    <ForwardedIconComponent
                      name="loader-circle"
                      className="h-4 w-4 mr-2 animate-spin"
                    />
                    로딩 중...
                  </>
                ) : (
                  <>
                    <ForwardedIconComponent
                      name="refresh-cw"
                      className="h-4 w-4 mr-2"
                    />
                    새로고침
                  </>
                )}
              </Button>
            )}

            {/* Traces List */}
            {isConnected && (
              <div className="flex flex-col gap-2">
                <div className="text-sm font-medium">최근 트레이스</div>

                {tracesLoading ? (
                  <div className="text-xs text-muted-foreground text-center py-4">
                    트레이스를 불러오는 중...
                  </div>
                ) : traces.length === 0 ? (
                  <div className="text-xs text-muted-foreground text-center py-4">
                    트레이스가 없습니다
                  </div>
                ) : (
                  <div className="flex flex-col gap-2">
                    {traces.map((trace) => (
                      <Card
                        key={trace.id}
                        className="overflow-hidden cursor-pointer hover:bg-accent transition-colors"
                        onClick={() => handleTraceClick(trace.id)}
                      >
                        <CardContent className="p-3">
                          <div className="flex flex-col gap-2">
                            <div className="flex items-start justify-between">
                              <div className="flex-1 min-w-0">
                                <div className="text-xs font-medium truncate">
                                  {trace.name || "Unnamed Trace"}
                                </div>
                                <div className="text-xs text-muted-foreground font-mono truncate">
                                  ID: {trace.id.slice(0, 8)}...
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center justify-between text-xs">
                              <div className="flex items-center gap-1 text-muted-foreground">
                                <ForwardedIconComponent
                                  name="clock"
                                  className="h-3 w-3"
                                />
                                {formatTimestamp(trace.timestamp)}
                              </div>
                              {trace.total_cost !== null && (
                                <div className="flex items-center gap-1 font-mono">
                                  <ForwardedIconComponent
                                    name="dollar-sign"
                                    className="h-3 w-3"
                                  />
                                  {formatCost(trace.total_cost)}
                                </div>
                              )}
                            </div>

                            {trace.metadata && (
                              <div className="text-xs text-muted-foreground">
                                {Object.keys(trace.metadata).length > 0 && (
                                  <span>
                                    메타데이터: {Object.keys(trace.metadata).length}개
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}

                    {tracesData?.has_more && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full text-xs"
                      >
                        더 보기
                      </Button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </SidebarGroupContent>
      </SidebarGroup>

      {/* Trace Detail Modal */}
      <Dialog open={!!selectedTraceId} onOpenChange={handleCloseModal}>
        <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
          <DialogHeader className="flex-shrink-0">
            <DialogTitle className="flex items-center gap-2">
              <ForwardedIconComponent name="activity" className="h-5 w-5" />
              트레이스 상세 정보
            </DialogTitle>
          </DialogHeader>

          <div className="overflow-y-auto flex-1">
            {traceDetailLoading ? (
              <div className="flex items-center justify-center py-12">
                <ForwardedIconComponent
                  name="loader-circle"
                  className="h-8 w-8 animate-spin text-muted-foreground"
                />
              </div>
            ) : traceDetail ? (
              <div className="flex flex-col gap-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-1">
                    Trace ID
                  </div>
                  <div className="text-sm font-mono bg-muted p-2 rounded">
                    {traceDetail.id}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-1">
                    Name
                  </div>
                  <div className="text-sm font-medium p-2">
                    {traceDetail.name || "Unnamed Trace"}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-1">
                    Timestamp
                  </div>
                  <div className="text-sm p-2">
                    {new Date(traceDetail.timestamp).toLocaleString("ko-KR")}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-1">
                    Total Cost
                  </div>
                  <div className="text-sm font-mono p-2">
                    {formatCost(traceDetail.total_cost)}
                  </div>
                </div>
                {traceDetail.user_id && (
                  <div>
                    <div className="text-sm font-medium text-muted-foreground mb-1">
                      User ID
                    </div>
                    <div className="text-sm font-mono p-2">
                      {traceDetail.user_id}
                    </div>
                  </div>
                )}
                {traceDetail.session_id && (
                  <div>
                    <div className="text-sm font-medium text-muted-foreground mb-1">
                      Session ID
                    </div>
                    <div className="text-sm font-mono p-2">
                      {traceDetail.session_id}
                    </div>
                  </div>
                )}
              </div>

              {/* Input */}
              {traceDetail.input && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-2">
                    Input
                  </div>
                  <pre className="text-xs bg-muted p-4 rounded overflow-x-auto">
                    {JSON.stringify(traceDetail.input, null, 2)}
                  </pre>
                </div>
              )}

              {/* Output */}
              {traceDetail.output && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-2">
                    Output
                  </div>
                  <pre className="text-xs bg-muted p-4 rounded overflow-x-auto">
                    {JSON.stringify(traceDetail.output, null, 2)}
                  </pre>
                </div>
              )}

              {/* Metadata */}
              {traceDetail.metadata &&
                Object.keys(traceDetail.metadata).length > 0 && (
                  <div>
                    <div className="text-sm font-medium text-muted-foreground mb-2">
                      Metadata
                    </div>
                    <pre className="text-xs bg-muted p-4 rounded overflow-x-auto">
                      {JSON.stringify(traceDetail.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                트레이스를 불러올 수 없습니다
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
