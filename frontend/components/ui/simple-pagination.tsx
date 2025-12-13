import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationEllipsis,
} from "./pagination";
import { getPaginationRange } from "./pagination";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./select";

function SimplePagination({
  page = 1,
  totalPages,
  onPageChange = () => {},
  pageSize = 10,
  onPageSizeChange = () => {},
}: {
  page: number;
  totalPages: number;
  pageSize?: number;
  onPageChange?: (newPage: number) => void;
  onPageSizeChange?: (newPageSize: number) => void;
}) {
  const range = getPaginationRange(page, totalPages);

  const handlePageChange = (newPage: number) => {
    onPageChange(newPage);
  };
  return (
    <div className="flex items-center justify-between gap-2">
      <Pagination>
        <PaginationContent>
          {range.map((item, index) => (
            <PaginationItem key={index}>
              {item === "ellipsis" ? (
                <PaginationEllipsis />
              ) : (
                <PaginationLink
                  onClick={() => handlePageChange(item as number)}
                  {...(item === page && { isActive: true })}
                >
                  {item}
                </PaginationLink>
              )}
            </PaginationItem>
          ))}
        </PaginationContent>
      </Pagination>
      <div className="flex items-center gap-2">
        <Select
          defaultValue={pageSize.toString()}
          onValueChange={(value) => onPageSizeChange(Number(value))}
        >
          <SelectTrigger>
            <SelectValue placeholder="halaman" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="10">10</SelectItem>
            <SelectItem value="25">25</SelectItem>
            <SelectItem value="50">50</SelectItem>
            <SelectItem value="100">100</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}

export default SimplePagination;
