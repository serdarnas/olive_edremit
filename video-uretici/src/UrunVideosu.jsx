import React from "react";
import {
	AbsoluteFill,
	Audio,
	Img,
	interpolate,
	spring,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
} from "remotion";
import {createTikTokStyleCaptions, parseSrt} from "@remotion/captions";

// Bu bileşen hiçbir sayı/cümle uydurmaz — fiyat/indirim yalnız props'tan (veri/YYYY-Www.json
// kaynaklı), altyazı yalnız edge-tts'in ürettiği SRT metninden gelir. bkz. ANAYASA §2.

const bicimFiyat = (deger, paraBirimi) => {
	if (deger === null || deger === undefined) return null;
	return `${Number(deger).toLocaleString("tr-TR")} ${paraBirimi || "TL"}`;
};

const FiyatEtiketi = ({fiyat, indirim, indirimOran, paraBirimi}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	if (indirimOran === null || indirimOran === undefined) return null;
	const giris = spring({frame: frame - Math.round(fps * 0.5), fps, config: {damping: 14}});
	return (
		<div
			style={{
				position: "absolute",
				top: 140,
				right: 40,
				background: "#1b3a2f",
				color: "white",
				borderRadius: 20,
				padding: "18px 26px",
				transform: `scale(${giris})`,
				opacity: giris,
				fontFamily: "sans-serif",
				textAlign: "center",
				boxShadow: "0 8px 24px rgba(0,0,0,0.35)",
			}}
		>
			<div style={{fontSize: 40, fontWeight: 800}}>%{indirimOran} İndirim</div>
			{indirim !== null && indirim !== undefined && (
				<div style={{fontSize: 28, marginTop: 6}}>
					{fiyat !== null && fiyat !== undefined && (
						<span style={{textDecoration: "line-through", opacity: 0.6, marginRight: 10}}>
							{bicimFiyat(fiyat, paraBirimi)}
						</span>
					)}
					<span style={{fontWeight: 700}}>{bicimFiyat(indirim, paraBirimi)}</span>
				</div>
			)}
		</div>
	);
};

const Altyazi = ({altyaziSrtMetni}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const simdiMs = (frame / fps) * 1000;
	if (!altyaziSrtMetni) return null;
	const {captions} = parseSrt({input: altyaziSrtMetni});
	if (!captions.length) return null;
	const {pages} = createTikTokStyleCaptions({captions, combineTokensWithinMilliseconds: 1200});
	const sayfa = pages.find((s) => simdiMs >= s.startMs && simdiMs < s.startMs + s.durationMs);
	if (!sayfa) return null;
	return (
		<div
			style={{
				position: "absolute",
				bottom: 160,
				left: 60,
				right: 60,
				textAlign: "center",
				fontFamily: "sans-serif",
				fontSize: 52,
				fontWeight: 800,
				color: "white",
				textShadow: "0 2px 10px rgba(0,0,0,0.8)",
			}}
		>
			{sayfa.tokens.map((jeton, i) => {
				const aktif = simdiMs >= jeton.fromMs && simdiMs < jeton.toMs;
				return (
					<span key={i} style={{color: aktif ? "#ffd23f" : "white", marginRight: 12}}>
						{jeton.text}
					</span>
				);
			})}
		</div>
	);
};

export const UrunVideosu = ({
	gorselYolu,
	sesYolu,
	altyaziSrtMetni,
	fiyat,
	indirim,
	indirimOran,
	paraBirimi,
}) => {
	const frame = useCurrentFrame();
	const {durationInFrames} = useVideoConfig();
	const olcek = interpolate(frame, [0, durationInFrames], [1, 1.08]);
	return (
		<AbsoluteFill style={{backgroundColor: "black"}}>
			{gorselYolu && (
				<Img
					src={staticFile(gorselYolu)}
					style={{
						width: "100%",
						height: "100%",
						objectFit: "cover",
						transform: `scale(${olcek})`,
					}}
				/>
			)}
			<FiyatEtiketi fiyat={fiyat} indirim={indirim} indirimOran={indirimOran} paraBirimi={paraBirimi} />
			<Altyazi altyaziSrtMetni={altyaziSrtMetni} />
			{sesYolu && <Audio src={staticFile(sesYolu)} />}
		</AbsoluteFill>
	);
};
