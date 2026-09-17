import React from "react";
import {Composition} from "remotion";
import {UrunVideosu} from "./UrunVideosu.jsx";

const FPS = 30;
const VARSAYILAN_SURE_SN = 12;

export const RemotionRoot = () => {
	return (
		<Composition
			id="UrunVideosu"
			component={UrunVideosu}
			fps={FPS}
			width={1080}
			height={1920}
			durationInFrames={Math.round(VARSAYILAN_SURE_SN * FPS)}
			defaultProps={{
				gorselYolu: null,
				sesYolu: null,
				altyaziSrtMetni: null,
				baslik: "",
				fiyat: null,
				indirim: null,
				indirimOran: null,
				paraBirimi: "TL",
				sureSaniye: VARSAYILAN_SURE_SN,
			}}
			calculateMetadata={async ({props}) => {
				const sure = props.sureSaniye || VARSAYILAN_SURE_SN;
				return {durationInFrames: Math.round(sure * FPS)};
			}}
		/>
	);
};
