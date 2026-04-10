import { useState } from "react";
import { Input } from "./input";
import { Button } from "./button";
import { EyeIcon, EyeSlashIcon } from "@heroicons/react/24/outline";

export function InputPassword({ ...props }: React.ComponentProps<"input">) {
    const [showPassword, setShowPassword] = useState(false);

    const handleShowPassword = (e: React.MouseEvent<HTMLButtonElement>) => {
        e.preventDefault();
        setShowPassword(!showPassword);
    }

    return (
        <div className="relative">
            <Input type={showPassword ? "text" : "password"} className="pr-10" {...props} />
            <Button variant="ghost" size="icon" className="absolute right-2 top-1/2 -translate-y-1/2" onClick={handleShowPassword}>
                {showPassword ? <EyeSlashIcon className="w-4 h-4" /> : <EyeIcon className="w-4 h-4" />}
            </Button>
        </div>
    );
}