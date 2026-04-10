export function AvatarLetter({ letter }: { letter: string }) {
  return (
    <div className="w-8 h-8 rounded-full bg-brand-primary text-white flex items-center justify-center">
      <span className="text-xs uppercase">{letter}</span>
    </div>
  );
}