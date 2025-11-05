import { Progress } from "@/components/ui/progress";
import { Card } from "@/components/ui/card";
import { Loader2, Sparkles, CheckCircle, XCircle } from "lucide-react";

interface GenerationProgressProps {
  isGenerating: boolean;
  progress: number;
  stage: string;
  currentStep: number;
  totalSteps: number;
  error?: string;
}

const GenerationProgress = ({
  isGenerating,
  progress,
  stage,
  currentStep,
  totalSteps,
  error
}: GenerationProgressProps) => {
  if (!isGenerating && !error) {
    return null;
  }

  const getStageIcon = () => {
    if (error) {
      return <XCircle className="h-5 w-5 text-red-500" />;
    }
    
    if (progress >= 100) {
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    }
    
    return <Loader2 className="h-5 w-5 animate-spin text-primary" />;
  };

  const getStageColor = () => {
    if (error) return "text-red-600";
    if (progress >= 100) return "text-green-600";
    return "text-primary";
  };

  const getProgressColor = () => {
    if (error) return "bg-red-500";
    if (progress >= 100) return "bg-green-500";
    return "bg-primary";
  };

  return (
    <Card className="p-6 bg-gradient-card border-border shadow-card">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center gap-3">
          {getStageIcon()}
          <div className="flex-1">
            <h3 className="font-semibold text-lg">
              {error ? "Generation Failed" : "Generating Image"}
            </h3>
            <p className={`text-sm ${getStageColor()}`}>
              {error || stage}
            </p>
          </div>
          {!error && (
            <div className="text-right">
              <div className="text-2xl font-bold text-primary">
                {Math.round(progress)}%
              </div>
              {totalSteps > 0 && (
                <div className="text-sm text-muted-foreground">
                  Step {currentStep}/{totalSteps}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Progress Bar */}
        {!error && (
          <div className="space-y-2">
            <Progress 
              value={progress} 
              className="h-3"
              style={{
                background: "var(--muted)",
              }}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0%</span>
              <span>100%</span>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Stage Indicators */}
        {!error && (
          <div className="grid grid-cols-4 gap-2 text-xs">
            {[
              { name: "Loading", range: [0, 10] },
              { name: "Preparing", range: [10, 15] },
              { name: "Generating", range: [15, 95] },
              { name: "Finishing", range: [95, 100] },
            ].map((stageInfo, index) => {
              const isActive = progress >= stageInfo.range[0] && progress < stageInfo.range[1];
              const isCompleted = progress >= stageInfo.range[1];
              
              return (
                <div
                  key={index}
                  className={`p-2 rounded text-center transition-colors ${
                    isActive
                      ? "bg-primary/20 text-primary border border-primary/30"
                      : isCompleted
                      ? "bg-green-100 text-green-700 border border-green-200"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {stageInfo.name}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Card>
  );
};

export default GenerationProgress;