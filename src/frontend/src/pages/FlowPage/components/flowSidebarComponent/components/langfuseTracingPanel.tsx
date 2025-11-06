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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
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

  const handleCopyJson = (data: any) => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
  };

  const calculateDuration = (obj: any): string | null => {
    if (obj && typeof obj === "object" && obj.startTime && obj.endTime) {
      try {
        const start = new Date(obj.startTime).getTime();
        const end = new Date(obj.endTime).getTime();
        const duration = end - start;

        if (duration < 1000) {
          return `${duration}ms`;
        } else {
          return `${(duration / 1000).toFixed(2)}s`;
        }
      } catch {
        return null;
      }
    }
    return null;
  };

  const renderJsonValue = (value: any, depth: number = 0): React.ReactNode => {
    if (value === null || value === undefined) {
      return <span className="text-muted-foreground italic">null</span>;
    }
    if (typeof value === "boolean") {
      return <span className="text-foreground">{String(value)}</span>;
    }
    if (typeof value === "number") {
      return <span className="text-foreground">{value}</span>;
    }
    if (typeof value === "string") {
      return <span className="text-muted-foreground break-all">"{value}"</span>;
    }
    if (Array.isArray(value)) {
      return (
        <div className="ml-4 space-y-1">
          {value.map((item, idx) => (
            <div key={idx} className="flex flex-col gap-1">
              <span className="text-muted-foreground text-xs">[{idx}]</span>
              <div className="ml-2">{renderJsonValue(item, depth + 1)}</div>
            </div>
          ))}
        </div>
      );
    }
    if (typeof value === "object") {
      const entries = Object.entries(value);
      return (
        <div className={depth === 0 ? "space-y-3" : "ml-4 space-y-2"}>
          {entries.map(([key, val]) => {
            const duration = depth === 0 ? calculateDuration(val) : null;
            return (
              <div
                key={key}
                className={depth === 0 ? "bg-muted/50 p-3 rounded-md border border-border/50 relative" : "flex flex-col gap-1"}
              >
                {depth === 0 ? (
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-foreground font-semibold text-base break-all">
                      {key}
                    </span>
                    {duration && (
                      <span className="text-muted-foreground text-xs font-mono whitespace-nowrap">
                        {duration}
                      </span>
                    )}
                  </div>
                ) : (
                  <span className="text-foreground font-medium break-all">
                    {key}:
                  </span>
                )}
                <div className={depth === 0 ? "" : "ml-2"}>{renderJsonValue(val, depth + 1)}</div>
              </div>
            );
          })}
        </div>
      );
    }
    return String(value);
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
                    {traces.map((trace: any) => (
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
              <div className="flex flex-col gap-4">
                {/* Basic Info */}
                <div className="bg-muted/30 p-4 rounded-lg space-y-3 text-sm">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-muted-foreground">Timestamp:</span>
                      <span className="ml-2">
                        {new Date(traceDetail.timestamp).toLocaleString("ko-KR")}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Cost:</span>
                      <span className="ml-2 font-mono">{formatCost(traceDetail.total_cost)}</span>
                    </div>
                    {traceDetail.metadata?.time_elapsed && (
                      <div>
                        <span className="text-muted-foreground">time elapsed:</span>
                        <span className="ml-2 font-mono">
                          {typeof traceDetail.metadata.time_elapsed === 'number'
                            ? `${traceDetail.metadata.time_elapsed.toFixed(2)}s`
                            : traceDetail.metadata.time_elapsed}
                        </span>
                      </div>
                    )}
                    {traceDetail.session_id && (
                      <div>
                        <span className="text-muted-foreground">Session ID:</span>
                        <span className="ml-2 font-mono">{traceDetail.session_id}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Tabs for Input/Output/Metadata */}
                <Tabs defaultValue="input" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="input" className="gap-2">
                      <ForwardedIconComponent name="arrow-down-to-line" className="h-3.5 w-3.5" />
                      Input
                    </TabsTrigger>
                    <TabsTrigger value="output" className="gap-2">
                      <ForwardedIconComponent name="arrow-up-from-line" className="h-3.5 w-3.5" />
                      Output
                    </TabsTrigger>
                    <TabsTrigger value="metadata" className="gap-2">
                      <ForwardedIconComponent name="info" className="h-3.5 w-3.5" />
                      Metadata
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="input" className="mt-4">
                    {traceDetail.input ? (
                      <div className="relative group">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => handleCopyJson(traceDetail.input)}
                        >
                          <ForwardedIconComponent name="copy" className="h-4 w-4" />
                        </Button>
                        <div className="bg-muted/30 p-4 rounded-lg border border-border text-sm">
                          {renderJsonValue(traceDetail.input)}
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-muted-foreground text-sm">
                        <ForwardedIconComponent name="inbox" className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        Input 데이터가 없습니다
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="output" className="mt-4">
                    {traceDetail.output ? (
                      <div className="relative group">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => handleCopyJson(traceDetail.output)}
                        >
                          <ForwardedIconComponent name="copy" className="h-4 w-4" />
                        </Button>
                        <div className="bg-muted/30 p-4 rounded-lg border border-border text-sm">
                          {renderJsonValue(traceDetail.output)}
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-muted-foreground text-sm">
                        <ForwardedIconComponent name="inbox" className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        Output 데이터가 없습니다
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="metadata" className="mt-4">
                    <div className="relative group">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={() => handleCopyJson({
                          id: traceDetail.id,
                          name: traceDetail.name,
                          user_id: traceDetail.user_id,
                          ...traceDetail.metadata
                        })}
                      >
                        <ForwardedIconComponent name="copy" className="h-4 w-4" />
                      </Button>
                      <div className="bg-muted/30 p-4 rounded-lg border border-border text-sm space-y-3">
                        {/* ID */}
                        <div className="bg-muted/50 p-3 rounded-md border border-border/50">
                            <div className="flex flex-col gap-1">
                              <span className="text-foreground font-medium">ID:</span>
                              <span className="ml-2 font-mono text-muted-foreground break-all">{traceDetail.id}</span>
                            </div>
                        </div>

                        {/* Name */}
                        <div className="bg-muted/50 p-3 rounded-md border border-border/50">
                            <div className="flex flex-col gap-1">
                              <span className="text-foreground font-medium">Name:</span>
                              <span className="ml-2 text-muted-foreground break-all">{traceDetail.name || "Unnamed"}</span>
                            </div>
                        </div>

                        {/* User ID */}
                        {traceDetail.user_id && (
                          <div className="bg-muted/50 p-3 rounded-md border border-border/50">
                            <div className="flex flex-col gap-1">
                              <span className="text-foreground font-medium">User ID:</span>
                              <span className="ml-2 font-mono text-muted-foreground break-all">{traceDetail.user_id}</span>
                          </div>
                        </div>
                        )}

                        {/* Other Metadata */}
                        {traceDetail.metadata && Object.keys(traceDetail.metadata).length > 0 ? (
                          renderJsonValue(traceDetail.metadata)
                        ) : (
                          <div className="text-center py-4 text-muted-foreground text-sm">
                            추가 메타데이터가 없습니다
                          </div>
                        )}
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
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
