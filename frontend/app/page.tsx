import Dropzone from "./components/DragnDrop";

export default function Home() {
  return (
    <>
      <Dropzone required={true} name="audio" />
    </>
  );
}
