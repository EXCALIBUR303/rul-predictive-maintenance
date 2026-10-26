// shadcn/ui-style owned primitive, composed with Radix Slot and CVA.
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { clsx } from 'clsx';
const variants=cva('rul-button',{variants:{variant:{default:'rul-button-primary',outline:'rul-button-outline',ghost:'rul-button-ghost'}},defaultVariants:{variant:'outline'}});
export function Button({asChild=false,variant,className,...props}:React.ComponentProps<'button'>&VariantProps<typeof variants>&{asChild?:boolean}) {const Comp=asChild?Slot:'button'; return <Comp className={clsx(variants({variant}),className)} {...props}/>;}
