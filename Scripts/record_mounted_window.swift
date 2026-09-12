// Apple's SCStream + AVAssetWriter. Capture only the explicitly supplied owned
// AshWell PID. Preserve original CMSampleBuffer timestamps and log every append.
import Foundation
import AppKit
import CoreGraphics
import ScreenCaptureKit
import AVFoundation

final class Capture: NSObject, SCStreamOutput, SCStreamDelegate {
    let writer: AVAssetWriter
    let video: AVAssetWriterInput
    let audio: AVAssetWriterInput
    let queue = DispatchQueue(label: "ashwell.native.capture")
    let ptsFile: FileHandle
    var started = false
    var requestedStop = false
    var error: Error?
    var origin = CMTime.invalid
    var startedUTC = ""
    var videoFrames = 0
    var audioBuffers = 0
    var droppedVideo = 0
    var droppedAudio = 0
    var received = 0
    init(url: URL, width: Int, height: Int) throws {
        writer = try AVAssetWriter(outputURL: url, fileType: .mp4)
        video = AVAssetWriterInput(mediaType: .video, outputSettings: [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: width, AVVideoHeightKey: height, AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 16_000_000, AVVideoExpectedSourceFrameRateKey: 60, AVVideoMaxKeyFrameIntervalKey: 120]])
        audio = AVAssetWriterInput(mediaType: .audio, outputSettings: [AVFormatIDKey: kAudioFormatMPEG4AAC, AVSampleRateKey: 48000, AVNumberOfChannelsKey: 2, AVEncoderBitRateKey: 192000])
        video.expectsMediaDataInRealTime = true; audio.expectsMediaDataInRealTime = true
        guard writer.canAdd(video), writer.canAdd(audio) else { throw NSError(domain: "Native writer rejected output settings", code: 1) }
        writer.add(video); writer.add(audio)
        let p = url.deletingPathExtension().appendingPathExtension("samples.csv")
        FileManager.default.createFile(atPath: p.path, contents: Data("type,pts_value,pts_timescale,host_seconds,appended\n".utf8))
        ptsFile = try FileHandle(forWritingTo: p)
        try ptsFile.seekToEnd()
        super.init()
    }
    func stream(_ stream: SCStream, didStopWithError error: Error) { self.error = error }
    func stream(_ stream: SCStream, didOutputSampleBuffer buffer: CMSampleBuffer, of type: SCStreamOutputType) {
        received += 1
        if received <= 8 { print("NATIVE_SAMPLE type=\(type.rawValue) valid=\(buffer.isValid) ready=\(CMSampleBufferDataIsReady(buffer)) attachments=\(String(describing: CMSampleBufferGetSampleAttachmentsArray(buffer, createIfNecessary: false)))"); fflush(stdout) }
        guard buffer.isValid else { return }
        if type == .screen {
            guard let attachments = CMSampleBufferGetSampleAttachmentsArray(buffer, createIfNecessary: false) as? [[SCStreamFrameInfo: Any]], let status = attachments.first?[.status] as? Int, status == SCFrameStatus.complete.rawValue, CMSampleBufferGetImageBuffer(buffer) != nil else { return }
        } else if type != .audio { return }
        let pts = CMSampleBufferGetPresentationTimeStamp(buffer)
        guard pts.isValid else { return }
        if !started {
            guard type == .screen else { return }
            guard writer.startWriting() else { error = writer.error; return }
            origin = pts; writer.startSession(atSourceTime: pts); started = true
            let f = ISO8601DateFormatter(); f.formatOptions = [.withInternetDateTime,.withFractionalSeconds]; startedUTC = f.string(from: Date())
            print("NATIVE_RECORDING_STARTED " + startedUTC); fflush(stdout)
        }
        guard pts >= origin else { return }
        let input = type == .screen ? video : audio
        var appended = false
        if input.isReadyForMoreMediaData { appended = input.append(buffer) }
        if type == .screen { if appended { videoFrames += 1 } else { droppedVideo += 1 } }
        else { if appended { audioBuffers += 1 } else { droppedAudio += 1 } }
        if writer.status == .failed { error = writer.error }
        let row = "\(type == .screen ? "video" : "audio"),\(pts.value),\(pts.timescale),\(ProcessInfo.processInfo.systemUptime),\(appended)\n"
        ptsFile.write(Data(row.utf8))
    }
    func finish() async {
        await withCheckedContinuation { (c: CheckedContinuation<Void,Never>) in
            queue.async {
                guard self.started else { c.resume(); return }
                self.video.markAsFinished(); self.audio.markAsFinished()
                self.writer.finishWriting { c.resume() }
            }
        }
        try? ptsFile.close()
    }
}

@main struct Main {
    @MainActor static func main() async {
        do {
            let app = NSApplication.shared; app.setActivationPolicy(.prohibited)
            let args = CommandLine.arguments
            guard args.count == 4, let pid = Int32(args[1]), let seconds = Double(args[3]), seconds > 0, seconds <= 1200 else { throw NSError(domain: "Usage: record_mounted_window PID OUTPUT.mp4 SECONDS", code: 1) }
            guard CGPreflightScreenCaptureAccess() else { throw NSError(domain: "Screen recording permission unavailable; user action required. No bypass attempted.", code: 2) }
            let url = URL(fileURLWithPath: args[2]); guard !FileManager.default.fileExists(atPath: url.path) else { throw NSError(domain: "Refusing to overwrite a recording", code: 3) }
            let content = try await SCShareableContent.excludingDesktopWindows(true, onScreenWindowsOnly: true)
            guard !content.displays.isEmpty else { throw NSError(domain: "No capturable display. Unlock or wake the Mac before recording.", code: 8) }
            let windows = content.windows.filter { $0.owningApplication?.processID == pid && $0.title?.contains("AshWell") == true && $0.frame.width > 600 }
            guard windows.count == 1, let window = windows.first else { throw NSError(domain: "Expected one visible AshWell window for specified owned PID", code: 4) }
            print("NATIVE_WINDOW_FRAME \(window.frame) display_frames=\(content.displays.map { String(describing: $0.frame) + " size=" + String($0.width) + "x" + String($0.height) })"); fflush(stdout)
            guard let display = content.displays.first(where: { $0.frame.intersects(window.frame) }) else { throw NSError(domain: "Selected window has no visible display", code: 7) }
            // Capture the composed Metal window. All other windows, the desktop
            // and dock are excluded by this inclusion filter.
            let filter = SCContentFilter(display: display, including: [window])
            filter.includeMenuBar = false
            let config = SCStreamConfiguration()
            config.width = Int(window.frame.width.rounded()); config.height = Int(window.frame.height.rounded())
            config.sourceRect = window.frame.offsetBy(dx: -display.frame.minX, dy: -display.frame.minY)
            config.minimumFrameInterval = CMTime(value: 1, timescale: 60); config.queueDepth = 5
            config.pixelFormat = kCVPixelFormatType_32BGRA
            config.showsCursor = true; config.ignoreShadowsSingleWindow = true
            config.capturesAudio = true; config.captureMicrophone = false; config.excludesCurrentProcessAudio = true; config.sampleRate = 48000; config.channelCount = 2
            let capture = try Capture(url: url, width: config.width, height: config.height)
            signal(SIGTERM, SIG_IGN); signal(SIGINT, SIG_IGN)
            let term = DispatchSource.makeSignalSource(signal: SIGTERM, queue: .main)
            let interrupt = DispatchSource.makeSignalSource(signal: SIGINT, queue: .main)
            term.setEventHandler { capture.requestedStop = true }; term.resume()
            interrupt.setEventHandler { capture.requestedStop = true }; interrupt.resume()
            let stream = SCStream(filter: filter, configuration: config, delegate: capture)
            try stream.addStreamOutput(capture, type: .screen, sampleHandlerQueue: capture.queue)
            try stream.addStreamOutput(capture, type: .audio, sampleHandlerQueue: capture.queue)
            let start = Date(); print("NATIVE_RECORDING_WINDOW pid=\(pid) pixels=\(config.width)x\(config.height) microphone=false")
            try await stream.startCapture()
            for _ in 0..<100 { if capture.started || capture.error != nil { break }; try await Task.sleep(nanoseconds: 100_000_000) }
            guard capture.started else { try? await stream.stopCapture(); throw capture.error ?? NSError(domain: "No complete video frame in ten seconds", code: 5) }
            let deadline = Date().addingTimeInterval(seconds)
            while Date() < deadline && !capture.requestedStop && capture.error == nil { try await Task.sleep(nanoseconds: 100_000_000) }
            try? await stream.stopCapture(); await capture.finish()
            let data: [String: Any] = ["pid": pid, "window_title": window.title ?? "", "width": config.width, "height": config.height, "requested_fps": 60, "requested_seconds": seconds, "started_utc": capture.startedUTC, "wall_seconds": Date().timeIntervalSince(start), "video_frames": capture.videoFrames, "audio_buffers": capture.audioBuffers, "dropped_video_buffers": capture.droppedVideo, "dropped_audio_buffers": capture.droppedAudio, "writer_status": capture.writer.status.rawValue, "microphone": false, "source": "SCStream includes only selected owned window; AVAssetWriter receives original CMSampleBuffer PTS", "retiming": false, "interpolation": false, "stop_requested": capture.requestedStop, "stream_error": capture.error.map { String(describing: $0) } ?? ""]
            try JSONSerialization.data(withJSONObject: data, options: [.prettyPrinted,.sortedKeys]).write(to: url.deletingPathExtension().appendingPathExtension("capture.json"))
            guard capture.writer.status == .completed else { throw capture.writer.error ?? NSError(domain: "Writer did not complete", code: 6) }
            print("NATIVE_RECORDING_FINISHED frames=\(capture.videoFrames) audio=\(capture.audioBuffers)")
        } catch { fputs("NATIVE_RECORDING_BLOCKED: \(error)\n", stderr); exit(1) }
    }
}
