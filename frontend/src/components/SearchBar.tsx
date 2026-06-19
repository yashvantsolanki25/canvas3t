import { FormEvent, useEffect, useState } from "react";
import { useGalleryStore } from "../store/galleryStore";

const SearchBar = () => {
  const { search, setSearch } = useGalleryStore();
  const [value, setValue] = useState(search);

  useEffect(() => {
    setValue(search);
  }, [search]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setSearch(value);
  };

  return (
    <form className="search-bar" onSubmit={submit}>
      <input
        aria-label="Search paintings"
        placeholder="Search by title, id, tag..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      <button type="submit">Search</button>
    </form>
  );
};

export default SearchBar;

