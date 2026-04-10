import { Checkbox } from "../ui/checkbox";
import { CardSelectableProps } from "./card-selectable.types";
import { FormControl, FormField, FormItem, FormLabel } from "../ui/form";
import { CardItem } from "../card-item/card-item";

export function CardSelectable({
  id,
  title,
  description,
  footer,
  control,
  chunkDescription,
  detail,
  author,
}: CardSelectableProps) {
  return (
    <FormField
      control={control}
      name="options"
      render={({ field }) => {
        const checked = field.value?.includes(id);

        const toggle = (val: boolean) => {
          if (val) {
            field.onChange([...field.value, id]);
          } else {
            field.onChange(field.value.filter((v: string) => v !== id));
          }
        };

        return (
          <FormItem>
            <CardItem 
              title={
                <>
                <FormControl>
                <Checkbox
                  id={id}
                  checked={checked}
                  onCheckedChange={(val) => toggle(val === true)}
                />
              </FormControl>
              <FormLabel>{title}</FormLabel>
              </>
              } 
              description={description} 
              footer={footer} 
              chunkDescription={chunkDescription}
              detail={detail}
              author={author} />
          </FormItem>
        );
      }}
    />
  );
}
