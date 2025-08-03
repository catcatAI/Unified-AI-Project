import { Button } from '@/components/ui/button';
import { ModeToggle } from '@/components/mode-toggle';
import { Settings, User } from 'lucide-react';

export function Header() {
  return (
    <header className="h-16 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-full items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-foreground">
            統一AI專案控制台
          </h2>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon">
            <Settings className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon">
            <User className="h-4 w-4" />
          </Button>
          <ModeToggle />
        </div>
      </div>
    </header>
  );
}