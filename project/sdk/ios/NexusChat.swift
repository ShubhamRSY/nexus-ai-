import Foundation

/// Minimal Nexus chat client for iOS — wraps REST /chat API.
public final class NexusChat {
    public let apiBase: URL
    public var token: String
    public var sessionId: String

    public init(apiBase: URL, token: String, sessionId: String = UUID().uuidString) {
        self.apiBase = apiBase
        self.token = token
        self.sessionId = sessionId
    }

    public func send(message: String) async throws -> String {
        var req = URLRequest(url: apiBase.appendingPathComponent("chat"))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        let body: [String: String] = [
            "message": message,
            "session_id": sessionId,
            "agent_id": "chat_support",
        ]
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, _) = try await URLSession.shared.data(for: req)
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        return json?["response"] as? String ?? ""
    }
}
