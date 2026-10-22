import os
import json
import base64
import asyncio
import cv2
import httpx
from typing import List, Dict, Any, Tuple, Optional
from pydantic import ValidationError

from ..config import settings
from ..schemas import VisionAnalysisOutput, VisionActivityItem

class AIAnalyzer:
    @staticmethod
    def _encode_image_to_base64(image_path: str, max_dimension: int = 960) -> str:
        """
        Loads an image from disk, ensures reasonable dimensions for cloud API transmission,
        and returns JPEG base64-encoded string.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Frame file not found on disk: {image_path}")

        img = cv2.imread(image_path)
        if img is None:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

        h, w = img.shape[:2]
        if max(h, w) > max_dimension:
            scale = max_dimension / float(max(h, w))
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        ret, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if ret:
            return base64.b64encode(buf.tobytes()).decode('utf-8')

        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    @classmethod
    async def analyze_video_frames(
        cls,
        video_metadata: Dict[str, Any],
        sampled_frames: List[Dict[str, Any]],
        is_demo: bool = False,
        local_processing_only: bool = False,
        blur_faces: bool = False
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], str]:
        """
        Runs frame-by-frame visual understanding using configured vision provider:
        - "gemini": Google Gemini 1.5 Flash Vision API (official Google AI REST API)
        - "openai": OpenAI GPT-4o-mini Vision API (official OpenAI Chat Completions API)
        - "local_processing_only": 100% offline edge Computer Vision (Zero Cloud Transmission)
        Returns: (events, summary_data, model_name)
        """
        if not sampled_frames:
            raise ValueError("No video frames were extracted for analysis. Check video file validity.")

        # 1. Local Edge Processing Only Mode (Zero External Network Calls)
        if local_processing_only:
            model_label = "Local Edge CV (Privacy Mode - Zero Cloud Transmission)"
            events, summary = cls._analyze_with_local_cv(
                video_metadata,
                sampled_frames,
                is_demo,
                fallback_note="Local edge privacy mode active. No keyframes or telemetry transmitted outside device."
            )
            return events, summary, model_label

        provider = settings.AI_PROVIDER.lower().strip()

        # 2. Gemini Vision Provider
        if provider == "gemini":
            if not settings.GEMINI_API_KEY or not settings.GEMINI_API_KEY.strip():
                raise ValueError(
                    "Gemini API key is not configured. Please set GEMINI_API_KEY in your environment (.env) "
                    "or Settings to enable AI visual analysis."
                )
            return await cls._analyze_with_gemini(video_metadata, sampled_frames, blur_faces=blur_faces)

        # 3. OpenAI Vision Provider
        elif provider == "openai":
            if not settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY.strip():
                raise ValueError(
                    "OpenAI API key is not configured. Please set OPENAI_API_KEY in your environment (.env) "
                    "or Settings to enable AI visual analysis."
                )
            return await cls._analyze_with_openai(video_metadata, sampled_frames, blur_faces=blur_faces)

        # 4. No Supported Provider Configured (Never silently fake AI understanding)
        else:
            raise ValueError(
                f"No supported AI vision provider is configured (AI_PROVIDER='{provider}'). "
                "Please configure 'gemini' (with GEMINI_API_KEY) or 'openai' (with OPENAI_API_KEY) "
                "in Settings, or enable Local Edge CV Privacy Mode for offline processing."
            )

    @classmethod
    def _select_representative_frames(
        cls,
        sampled_frames: List[Dict[str, Any]],
        max_frames: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Selects a controlled number of representative frames covering the video timeline,
        prioritizing frames where foreground motion was detected while including baseline context.
        """
        valid_frames = [f for f in sampled_frames if os.path.exists(f.get("frame_path", ""))]
        if not valid_frames:
            raise ValueError("Sampled frame files are missing from storage directory.")

        if len(valid_frames) <= max_frames:
            return valid_frames

        # Separate motion-detected frames and quiet frames
        motion_frames = [f for f in valid_frames if f.get("motion_detected")]
        non_motion_frames = [f for f in valid_frames if not f.get("motion_detected")]

        selected = []
        if motion_frames:
            # Step evenly through motion frames
            step = max(1, len(motion_frames) // (max_frames - 2 if len(non_motion_frames) >= 2 else max_frames))
            for i in range(0, len(motion_frames), step):
                selected.append(motion_frames[i])
                if len(selected) >= max_frames - 2:
                    break

        # Fill remaining slots with evenly spaced baseline frames
        remaining_slots = max_frames - len(selected)
        if remaining_slots > 0 and non_motion_frames:
            step_nm = max(1, len(non_motion_frames) // remaining_slots)
            for j in range(0, len(non_motion_frames), step_nm):
                if non_motion_frames[j] not in selected:
                    selected.append(non_motion_frames[j])
                if len(selected) >= max_frames:
                    break

        # Fallback if still under target
        if len(selected) < min(max_frames, len(valid_frames)):
            for f in valid_frames:
                if f not in selected:
                    selected.append(f)
                if len(selected) >= max_frames:
                    break

        # Sort chronologically by timestamp
        selected.sort(key=lambda x: float(x.get("timestamp_sec", 0.0)))
        return selected

    @classmethod
    def _build_grounding_prompt(
        cls,
        duration: float,
        selected_frames: List[Dict[str, Any]]
    ) -> str:
        timestamps_info = ", ".join(
            f"Frame #{idx+1} at timestamp {f.get('time_str', '00:00')} ({f.get('timestamp_sec', 0.0):.1f}s)"
            for idx, f in enumerate(selected_frames)
        )

        return f"""You are an evidence-grounded home safety vision AI analyzing sampled keyframes from a home-security recording.
Total video duration: {duration:.1f} seconds.
Sampled keyframes provided ({len(selected_frames)} total):
{timestamps_info}

CRITICAL GROUNDING AND EVIDENCE RULES:
1. Describe ONLY visible actions directly supported by the supplied frames.
2. Use the supplied timestamps when describing events (start_time_seconds, end_time_seconds).
3. Distinguish direct visual observations from uncertain interpretations.
4. DO NOT attempt to identify a person's real-world identity or name.
5. DO NOT infer criminal intent, theft, trespassing, or an emergency without conclusive visual evidence.
6. DO NOT claim that a package was delivered unless the footage directly shows a package being deposited.
7. If evidence is insufficient to determine an activity or category, explicitly state that the activity cannot be determined and set category to "Uncertain".
8. Consolidate activities across adjacent frames to avoid repeatedly describing the same action.
9. Analysis is strictly based on sampled frames; clearly disclose uncertainty and do not claim continuous observation between widely spaced frames.
10. Return ONLY a single valid JSON object adhering strictly to this schema:
{{
  "summary": "Concise summary grounded purely in direct visual evidence.",
  "observed_activities": [
    "Chronological list of visible actions tied to specific timestamps"
  ],
  "important_time_ranges": [
    "00:04 - 00:11"
  ],
  "unknown_information": "Crucial details not verifiable from frames (e.g. identity, intent, vehicle license plate).",
  "recommended_review_action": "Practical homeowner recommendation (e.g. review clip if unexpected visitor).",
  "activities": [
    {{
      "start_time_seconds": 4.0,
      "end_time_seconds": 11.0,
      "category": "Person",
      "description": "A person in casual clothes walks toward the front door, pauses, and turns around.",
      "evidence": "Visible in frames at timestamps 00:04 and 00:08 near porch entrance.",
      "confidence": 0.92,
      "uncertainty": "Identity and reason for visit cannot be determined from sampled frames.",
      "review_priority": "Medium",
      "priority_reason": "Activity observed near the front entrance.",
      "location": "Front Door"
    }}
  ]
}}"""

    @classmethod
    def consolidate_vision_activities(
        cls,
        activities: List[VisionActivityItem],
        gap_tolerance: float = 2.0
    ) -> List[VisionActivityItem]:
        """
        Consolidates adjacent or overlapping observations of the same category
        so that repetitive events are not created for adjacent sampled frames.
        """
        if not activities:
            return []

        # Sort by category and start time
        sorted_acts = sorted(activities, key=lambda a: (a.category.lower(), a.start_time_seconds))
        consolidated: List[VisionActivityItem] = []

        for act in sorted_acts:
            if not consolidated:
                consolidated.append(act)
                continue

            prev = consolidated[-1]
            same_cat = prev.category.lower() == act.category.lower()
            time_gap = act.start_time_seconds - prev.end_time_seconds

            if same_cat and time_gap <= gap_tolerance:
                # Merge into single continuous interval
                new_end = max(prev.end_time_seconds, act.end_time_seconds)
                # Combine evidence notes
                combined_evidence = f"{prev.evidence}; {act.evidence}".strip("; ")
                # Take highest priority
                priorities = {"Low": 1, "Medium": 2, "High": 3}
                p_level = max(priorities.get(prev.review_priority, 1), priorities.get(act.review_priority, 1))
                new_priority = "High" if p_level == 3 else ("Medium" if p_level == 2 else "Low")

                # Combine uncertainty notes
                new_uncertainty = prev.uncertainty or act.uncertainty

                merged = VisionActivityItem(
                    start_time_seconds=min(prev.start_time_seconds, act.start_time_seconds),
                    end_time_seconds=new_end,
                    category=prev.category,
                    description=prev.description if len(prev.description) >= len(act.description) else act.description,
                    evidence=combined_evidence,
                    confidence=max(prev.confidence or 0.85, act.confidence or 0.85),
                    uncertainty=new_uncertainty,
                    review_priority=new_priority,
                    priority_reason=prev.priority_reason or act.priority_reason,
                    location=prev.location or act.location
                )
                consolidated[-1] = merged
            else:
                consolidated.append(act)

        # Re-sort chronologically by start time
        consolidated.sort(key=lambda a: a.start_time_seconds)
        return consolidated

    @classmethod
    def _extract_cv_motion_intervals(
        cls,
        video_metadata: Dict[str, Any],
        sampled_frames: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extracts independent OpenCV computer vision motion detection intervals.
        Kept separate from vision model outputs to preserve multi-modal evidence provenance.
        """
        raw_segments = []
        current_segment = None

        for f in sampled_frames:
            if f.get("motion_detected"):
                sec = float(f.get("timestamp_sec", 0.0))
                step = 1.0
                if current_segment is None:
                    current_segment = {
                        "category": "Motion",
                        "start_time": f.get("time_str", "00:00"),
                        "start_seconds": sec,
                        "end_time": f.get("time_str", "00:00"),
                        "end_seconds": sec + step,
                        "max_score": float(f.get("motion_score", 0.0)),
                        "thumbnail_path": f.get("frame_url")
                    }
                else:
                    current_segment["end_seconds"] = sec + step
                    mins = int(current_segment["end_seconds"] // 60)
                    secs = int(current_segment["end_seconds"] % 60)
                    current_segment["end_time"] = f"{mins:02d}:{secs:02d}"
                    if float(f.get("motion_score", 0.0)) > current_segment["max_score"]:
                        current_segment["max_score"] = float(f.get("motion_score", 0.0))
            else:
                if current_segment is not None:
                    raw_segments.append(current_segment)
                    current_segment = None

        if current_segment is not None:
            raw_segments.append(current_segment)

        merged = cls.group_motion_intervals(raw_segments, settings.MOTION_GROUPING_TOLERANCE_SECONDS)
        cv_events = []
        for seg in merged:
            is_high = seg["max_score"] > 0.45
            cv_events.append({
                "title": f"Motion detected ({seg['start_time']} - {seg['end_time']})",
                "category": "Motion",
                "start_time": seg["start_time"],
                "end_time": seg["end_time"],
                "start_seconds": seg["start_seconds"],
                "end_seconds": seg["end_seconds"],
                "description": f"Foreground movement observed between {seg['start_time']} and {seg['end_time']}. Motion contour score: {seg['max_score']:.2f}.",
                "priority": "Medium" if is_high else "Low",
                "priority_reason": "Foreground pixel displacement detected via OpenCV background subtraction.",
                "location": "Camera Zone",
                "confidence": None, # OpenCV optical contours do not provide semantic AI confidence
                "uncertainty": "Semantic object classification was not performed by OpenCV motion detector.",
                "thumbnail_path": seg.get("thumbnail_path"),
                "raw_evidence": f"Optical contour displacement score: {seg['max_score']:.2f}.",
                "detection_mode": "Local Motion Analysis",
                "source": "local_motion_cv"
            })
        return cv_events

    @classmethod
    async def _analyze_with_gemini(
        cls,
        video_metadata: Dict[str, Any],
        sampled_frames: List[Dict[str, Any]],
        blur_faces: bool = False
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], str]:
        """
        Sends sampled frames to Google Gemini 1.5 Flash Vision API with structured JSON output.
        """
        duration = float(video_metadata.get("duration", 20.0))
        selected_frames = cls._select_representative_frames(sampled_frames, max_frames=8)

        parts = []
        for f in selected_frames:
            b64 = cls._encode_image_to_base64(f["frame_path"])
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": b64
                }
            })

        prompt_text = cls._build_grounding_prompt(duration, selected_frames)
        parts.append({"text": prompt_text})

        model_name = getattr(settings, "clean_gemini_model", None)
        if not model_name:
            model_name = (settings.GEMINI_MODEL or "gemini-3.5-flash").strip()
            if model_name.startswith("models/"):
                model_name = model_name[len("models/"):]
        if not model_name:
            model_name = "gemini-3.5-flash"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        }

        # Resilient API invocation with retry on transient network/rate errors
        max_retries = 2
        last_error = None
        raw_text = None

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    break
            except httpx.HTTPStatusError as e:
                last_error = e
                # Retry on 429 rate limit or 5xx server error
                if e.response.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue

                # Parse clear error message from Google's response if JSON
                err_detail = e.response.text
                try:
                    err_json = e.response.json()
                    if isinstance(err_json, dict) and "error" in err_json:
                        err_detail = err_json["error"].get("message", e.response.text)
                except Exception:
                    pass

                if e.response.status_code == 404:
                    raise ValueError(
                        f"Gemini Vision API error (404): Model '{model_name}' was not found or is not supported for generateContent. "
                        f"Details: {err_detail}. Please configure a supported GEMINI_MODEL (e.g. 'gemini-3.5-flash')."
                    ) from e
                elif e.response.status_code in (401, 403):
                    raise ValueError(
                        f"Gemini Vision API authentication error ({e.response.status_code}): {err_detail}. "
                        "Please verify that GEMINI_API_KEY is valid and has access to the Generative Language API."
                    ) from e
                else:
                    raise ValueError(f"Gemini Vision API error ({e.response.status_code}): {err_detail}") from e
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                raise ValueError("Gemini Vision API request timed out after 60 seconds.") from e
            except Exception as e:
                if isinstance(e, ValueError):
                    raise
                raise ValueError(f"Failed to communicate with Gemini Vision API: {str(e)}") from e

        if not raw_text:
            raise ValueError(f"Empty response received from Gemini Vision API: {last_error}")

        # Parse & Validate structured output against Pydantic schema
        clean_text = raw_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()

        try:
            parsed_json = json.loads(clean_text)
            validated = VisionAnalysisOutput.model_validate(parsed_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Gemini returned invalid JSON: {clean_text[:200]}") from e
        except ValidationError as e:
            raise ValueError(f"Gemini structured output failed schema validation: {e}") from e

        # Consolidate activities to avoid duplicate descriptions across adjacent frames
        consolidated_acts = cls.consolidate_vision_activities(validated.activities)

        vision_events = []
        for idx, act in enumerate(consolidated_acts):
            s_mins = int(act.start_time_seconds // 60)
            s_secs = int(act.start_time_seconds % 60)
            e_mins = int(act.end_time_seconds // 60)
            e_secs = int(act.end_time_seconds % 60)
            time_start_str = f"{s_mins:02d}:{s_secs:02d}"
            time_end_str = f"{e_mins:02d}:{e_secs:02d}"

            # Pick thumbnail closest to start time
            closest = min(sampled_frames, key=lambda x: abs(float(x.get("timestamp_sec", 0.0)) - act.start_time_seconds))

            vision_events.append({
                "title": f"{act.category} detected ({time_start_str} - {time_end_str})",
                "category": act.category,
                "start_time": time_start_str,
                "end_time": time_end_str,
                "start_seconds": act.start_time_seconds,
                "end_seconds": act.end_time_seconds,
                "description": act.description,
                "priority": act.review_priority,
                "priority_reason": act.priority_reason or "Activity observed near camera zone.",
                "location": act.location or "Front Door",
                "confidence": act.confidence,
                "uncertainty": act.uncertainty or "Analysis based on sampled frames.",
                "raw_evidence": act.evidence,
                "thumbnail_path": closest.get("frame_url"),
                "detection_mode": "AI Visual Analysis",
                "source": "vision_ai"
            })

        # Also extract and append independent CV motion detection intervals
        cv_motion_events = cls._extract_cv_motion_intervals(video_metadata, sampled_frames)
        all_events = vision_events + cv_motion_events

        # Build grounded summary
        obs_text = "\n".join(f"• {act}" for act in validated.observed_activities) if validated.observed_activities else "Visual observations based on sampled frames."
        time_range_str = ", ".join(validated.important_time_ranges) if validated.important_time_ranges else f"00:00 - {int(duration//60):02d}:{int(duration%60):02d}"
        detected_objects_str = ", ".join(sorted(set([a.category for a in consolidated_acts]))) or "None specified"

        summary = {
            "overall_summary": validated.summary,
            "observations": obs_text,
            "time_range": time_range_str,
            "evidence": f"Analyzed {len(selected_frames)} keyframes via Gemini Vision ({model_name}). Face anonymization {'applied' if blur_faces else 'disabled'}.",
            "unknowns": validated.unknown_information,
            "uncertainty_limitations": validated.unknown_information,
            "review_rationale": f"Video analysis based on {len(selected_frames)} sampled keyframes across {duration:.1f}s footage.",
            "suggested_action": validated.recommended_review_action,
            "objects_detected": detected_objects_str,
            "frames_sampled": len(sampled_frames),
            "status": "Analyzed"
        }

        return all_events, summary, f"Gemini Vision ({model_name})"

    @classmethod
    async def _analyze_with_openai(
        cls,
        video_metadata: Dict[str, Any],
        sampled_frames: List[Dict[str, Any]],
        blur_faces: bool = False
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], str]:
        """
        Sends sampled frames to OpenAI GPT-4o-mini Vision API with structured JSON output.
        """
        duration = float(video_metadata.get("duration", 20.0))
        selected_frames = cls._select_representative_frames(sampled_frames, max_frames=8)

        prompt_text = cls._build_grounding_prompt(duration, selected_frames)
        content_parts = [{"type": "text", "text": prompt_text}]

        for f in selected_frames:
            b64 = cls._encode_image_to_base64(f["frame_path"])
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}",
                    "detail": "low"
                }
            })

        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [{"role": "user", "content": content_parts}],
            "response_format": {"type": "json_object"},
            "max_tokens": 1500,
            "temperature": 0.1
        }

        max_retries = 2
        last_error = None
        content_text = None

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    content_text = data["choices"][0]["message"]["content"]
                    break
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                raise ValueError(f"OpenAI Vision API error ({e.response.status_code}): {e.response.text}") from e
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                raise ValueError("OpenAI Vision API request timed out after 60 seconds.") from e
            except Exception as e:
                raise ValueError(f"Failed to communicate with OpenAI Vision API: {str(e)}") from e

        if not content_text:
            raise ValueError(f"Empty response received from OpenAI Vision API: {last_error}")

        try:
            parsed_json = json.loads(content_text)
            validated = VisionAnalysisOutput.model_validate(parsed_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"OpenAI returned invalid JSON: {content_text[:200]}") from e
        except ValidationError as e:
            raise ValueError(f"OpenAI structured output failed schema validation: {e}") from e

        consolidated_acts = cls.consolidate_vision_activities(validated.activities)

        vision_events = []
        for idx, act in enumerate(consolidated_acts):
            s_mins = int(act.start_time_seconds // 60)
            s_secs = int(act.start_time_seconds % 60)
            e_mins = int(act.end_time_seconds // 60)
            e_secs = int(act.end_time_seconds % 60)
            time_start_str = f"{s_mins:02d}:{s_secs:02d}"
            time_end_str = f"{e_mins:02d}:{e_secs:02d}"

            closest = min(sampled_frames, key=lambda x: abs(float(x.get("timestamp_sec", 0.0)) - act.start_time_seconds))

            vision_events.append({
                "title": f"{act.category} detected ({time_start_str} - {time_end_str})",
                "category": act.category,
                "start_time": time_start_str,
                "end_time": time_end_str,
                "start_seconds": act.start_time_seconds,
                "end_seconds": act.end_time_seconds,
                "description": act.description,
                "priority": act.review_priority,
                "priority_reason": act.priority_reason or "Activity observed near camera zone.",
                "location": act.location or "Front Door",
                "confidence": act.confidence,
                "uncertainty": act.uncertainty or "Analysis based on sampled frames.",
                "raw_evidence": act.evidence,
                "thumbnail_path": closest.get("frame_url"),
                "detection_mode": "AI Visual Analysis",
                "source": "vision_ai"
            })

        cv_motion_events = cls._extract_cv_motion_intervals(video_metadata, sampled_frames)
        all_events = vision_events + cv_motion_events

        obs_text = "\n".join(f"• {act}" for act in validated.observed_activities) if validated.observed_activities else "Visual observations based on sampled frames."
        time_range_str = ", ".join(validated.important_time_ranges) if validated.important_time_ranges else f"00:00 - {int(duration//60):02d}:{int(duration%60):02d}"
        detected_objects_str = ", ".join(sorted(set([a.category for a in consolidated_acts]))) or "None specified"

        summary = {
            "overall_summary": validated.summary,
            "observations": obs_text,
            "time_range": time_range_str,
            "evidence": f"Analyzed {len(selected_frames)} keyframes via OpenAI Vision ({settings.OPENAI_MODEL}). Face anonymization {'applied' if blur_faces else 'disabled'}.",
            "unknowns": validated.unknown_information,
            "uncertainty_limitations": validated.unknown_information,
            "review_rationale": f"Video analysis based on {len(selected_frames)} sampled keyframes across {duration:.1f}s footage.",
            "suggested_action": validated.recommended_review_action,
            "objects_detected": detected_objects_str,
            "frames_sampled": len(sampled_frames),
            "status": "Analyzed"
        }

        return all_events, summary, f"OpenAI Vision ({settings.OPENAI_MODEL})"

    @classmethod
    def group_motion_intervals(
        cls,
        raw_intervals: List[Dict[str, Any]],
        gap_tolerance: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Groups overlapping or adjacent motion intervals when they represent
        the same continuous motion. Intervals separated by more than gap_tolerance
        remain distinct events. Never merges differing categories.
        """
        if not raw_intervals:
            return []

        tolerance = gap_tolerance if gap_tolerance is not None else settings.MOTION_GROUPING_TOLERANCE_SECONDS

        sorted_intervals = sorted(
            raw_intervals,
            key=lambda x: (x.get("category", "Motion"), float(x.get("start_seconds", 0.0)))
        )
        merged = []

        for item in sorted_intervals:
            if not merged:
                merged.append(dict(item))
                continue

            prev = merged[-1]
            same_category = prev.get("category") == item.get("category")
            gap = float(item.get("start_seconds", 0.0)) - float(prev.get("end_seconds", 0.0))

            if same_category and gap <= tolerance:
                prev["end_seconds"] = max(float(prev.get("end_seconds", 0.0)), float(item.get("end_seconds", 0.0)))
                mins = int(prev["end_seconds"] // 60)
                secs = int(prev["end_seconds"] % 60)
                prev["end_time"] = f"{mins:02d}:{secs:02d}"
                prev["max_score"] = max(float(prev.get("max_score", 0.0)), float(item.get("max_score", 0.0)))
                if float(item.get("max_score", 0.0)) >= float(prev.get("max_score", 0.0)) and item.get("thumbnail_path"):
                    prev["thumbnail_path"] = item["thumbnail_path"]
            else:
                merged.append(dict(item))

        return merged

    @classmethod
    def _analyze_with_local_cv(
        cls,
        video_metadata: Dict[str, Any],
        sampled_frames: List[Dict[str, Any]],
        is_demo: bool = False,
        fallback_note: str = ""
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Evidence-grounded local processing using OpenCV MOG2 optical motion contours.
        Truthfully labels movement as motion without fabricating semantic classes
        like 'Person' or 'Vehicle'. Merges adjacent intervals using configurable gap tolerance.
        """
        duration = float(video_metadata.get("duration", 20.0))
        merged_segments = cls._extract_cv_motion_intervals(video_metadata, sampled_frames)

        events = []
        if not merged_segments:
            events.append({
                "title": "No significant activity",
                "category": "Motion",
                "start_time": "00:00",
                "end_time": f"{int(duration//60):02d}:{int(duration%60):02d}",
                "start_seconds": 0.0,
                "end_seconds": duration,
                "description": "Continuous ambient monitoring with no significant foreground motion detected.",
                "priority": "Low",
                "priority_reason": "Background subtraction detected no abnormal changes.",
                "location": "Camera Zone",
                "confidence": None,
                "uncertainty": "Continuous monitoring based on sampled keyframes.",
                "thumbnail_path": sampled_frames[0]["frame_url"] if sampled_frames else None,
                "raw_evidence": "OpenCV MOG2 background subtractor delta remained below movement threshold.",
                "detection_mode": "Local Motion Analysis",
                "source": "local_motion_cv"
            })
            summary_text = f"Continuous footage monitored across {duration:.1f} seconds. No significant foreground movement detected."
        else:
            events = merged_segments
            summary_text = f"Analyzed {len(sampled_frames)} frames across {duration:.1f}s. Detected {len(merged_segments)} motion interval(s). Review segments if activity was unexpected."

        summary = {
            "overall_summary": summary_text,
            "observations": f"• {len(sampled_frames)} frames sampled at 1.0s interval.\n• {len(merged_segments)} motion sequence(s) detected via background subtraction.\n" + (f"• Note: {fallback_note}" if fallback_note else ""),
            "time_range": f"00:00 - {int(duration//60):02d}:{int(duration%60):02d}",
            "evidence": f"Computed via OpenCV MOG2 optical delta. Resolution: {video_metadata.get('width')}x{video_metadata.get('height')}.",
            "unknowns": "Semantic object classes and human intent require a vision model (Gemini/OpenAI) configured in Settings.",
            "uncertainty_limitations": "Local Edge CV detects motion displacement only. Semantic object categories and intent are unverified.",
            "review_rationale": "Verify whether movement was caused by occupants, weather, or unknown visitors.",
            "suggested_action": "Check clip playback if movement occurred at an unexpected time.",
            "objects_detected": "Motion Contours",
            "frames_sampled": len(sampled_frames),
            "status": "Analyzed"
        }
        return events, summary
