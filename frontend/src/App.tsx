import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Chessboard } from "react-chessboard";
import { Chess, Move, Square, PieceSymbol, Color } from "chess.js";
import axios, { AxiosError } from "axios";
import "./App.css";

// —————————————————————————————————————————————————————————— Types
interface EngineConfig {
  elo: number;
  time: string;
}

interface GameState {
  fen: string;
  gameOver: boolean;
  result?: string;
  termination?: string;
  turn: "white" | "black";
  legalMoves: string[];
  lastMove?: string;
  moveHistory: string[];
  pgn?: string;
}

interface BestMove {
  move: string;
  san: string;
  rank: number;
  evaluation?: number;
  mate_in?: number;
  line?: string;
}

interface AnalysisResult {
  best_moves: BestMove[];
  position_type: "Opening" | "Middlegame" | "Endgame";
  turn: "white" | "black";
  evaluation: number; // centipawn evaluation
}

interface GameHistoryItem {
  id: number;
  start_time: string;
  end_time: string;
  result: string;
  white_player: string;
  black_player: string;
  engine_elo: number;
  total_moves: number;
  opening_name?: string;
}

interface MoveDetails {
  move_number: number;
  move_notation: string;
  fen_after: string;
  evaluation?: number;
  best_move?: string;
  timestamp: string;
}

// API Configuration
const API_BASE_URL = "http://127.0.0.1:5000";

// Colours for square highlights
const SELECT_COLOUR = "#ffce33aa";
const TARGET_COLOUR = "radial-gradient(circle, #ffff0055 36%, transparent 36%)";
const LAST_MOVE_COLOUR = "#88ff8833";
const CHECK_COLOUR = "#ff333366";

function findKingSquare(chess: Chess, color: Color): string | null {
  const board = chess.board();
  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
      const piece = board[row][col];
      if (piece && piece.type === 'k' && piece.color === color) {
        return String.fromCharCode(97 + col) + (8 - row);
      }
    }
  }
  return null;
}
// —————————————————————————————————————————————————————————— API Client
class ChessAPI {
  private static async handleError(error: AxiosError): Promise<never> {
    if (error.response?.data && typeof error.response.data === 'object' && 'error' in error.response.data) {
      throw new Error((error.response.data as {error: string}).error);
    }
    throw error;
  }

  static async initializeBoard(elo?: number, time?: number): Promise<GameState> {
    try {
      const params = new URLSearchParams();
      if (elo) params.append('elo', elo.toString());
      if (time) params.append('time', time.toString());
      
      const { data } = await axios.get(`${API_BASE_URL}/initialize-board?${params}`);
      return {
        fen: data.fen,
        gameOver: false,
        turn: data.turn,
        legalMoves: data.legal_moves || [],
        moveHistory: []
      };
    } catch (error) {
      return this.handleError(error as AxiosError);
    }
  }

  static async postMove(move: string): Promise<GameState> {
    try {
      const { data } = await axios.post(`${API_BASE_URL}/post-move`, { "new-move": move });
      return {
        fen: data.fen,
        gameOver: data.game_over,
        result: data.result,
        termination: data.termination,
        turn: data.turn,
        legalMoves: data.legal_moves || [],
        lastMove: data.last_move,
        moveHistory: data.move_history || [],
        pgn: data.pgn
      };
    } catch (error) {
      return this.handleError(error as AxiosError);
    }
  }

  static async engineMove(config: EngineConfig): Promise<GameState> {
    try {
      const { data } = await axios.post(`${API_BASE_URL}/engine-move`, config);
      return {
        fen: data.fen,
        gameOver: data.game_over,
        result: data.result,
        termination: data.termination,
        turn: data.turn,
        legalMoves: data.legal_moves || [],
        lastMove: data.last_move,
        moveHistory: data.move_history || [],
        pgn: data.pgn
      };
    } catch (error) {
      return this.handleError(error as AxiosError);
    }
  }

  static async getBestMoves(multipv?: number, time?: number): Promise<AnalysisResult> {
    try {
      const params = new URLSearchParams();
      if (multipv) params.append('multipv', multipv.toString());
      if (time) params.append('time', time.toString());
      
      const { data } = await axios.get(`${API_BASE_URL}/best-moves?${params}`);
      return data;
    } catch (error) {
      return this.handleError(error as AxiosError);
    }
  }

  static async getGameHistory(limit: number = 10, offset: number = 0): Promise<{
    games: GameHistoryItem[];
    total: number;
  }> {
    try {
      const { data } = await axios.get(`${API_BASE_URL}/game-history?limit=${limit}&offset=${offset}`);
      return data;
    } catch (error) {
      return this.handleError(error as AxiosError);
    }
  }

  static async analyzePosition(fen: string, depth: number = 20): Promise<any> {
    try {
      const { data } = await axios.post(`${API_BASE_URL}/analyze-position`, { fen, depth });
      return data;
    } catch (error) {
      return this.handleError(error as AxiosError);
    }
  }
}

// —————————————————————————————————————————————————————————— Components
interface AnalysisPanelProps {
  show: boolean;
  analysis: AnalysisResult | null;
  onClose: () => void;
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({ show, analysis, onClose }) => {
  if (!show || !analysis) return null;

  const formatEvaluation = (evaluation: number) => {
    if (evaluation > 0) {
      return `+${evaluation.toFixed(1)}`;
    } else if (evaluation < 0) {
      return `${evaluation.toFixed(1)}`;
    } else {
      return '0.0';
    }
  };

  return (
    <div className="analysis-panel">
      <button className="close-btn" onClick={onClose}>×</button>
      <h3>Position Evaluation</h3>
      <div className="evaluation-display">
        <div className="evaluation-item">
          <span className="player">White:</span>
          <span className="score">{formatEvaluation(analysis.evaluation)}</span>
        </div>
        <div className="evaluation-item">
          <span className="player">Black:</span>
          <span className="score">{formatEvaluation(-analysis.evaluation)}</span>
        </div>
      </div>
      <p className="position-type">{analysis.turn} to move</p>
    </div>
  );
};

interface GameHistoryPanelProps {
  show: boolean;
  onClose: () => void;
  onLoadGame?: (gameId: number) => void;
}

const GameHistoryPanel: React.FC<GameHistoryPanelProps> = ({ show, onClose, onLoadGame }) => {
  const [games, setGames] = useState<GameHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (show) {
      loadGames();
    }
  }, [show]);

  const loadGames = async () => {
    setLoading(true);
    try {
      const data = await ChessAPI.getGameHistory();
      setGames(data.games);
    } catch (error) {
      console.error("Failed to load games:", error);
    } finally {
      setLoading(false);
    }
  };

  if (!show) return null;

  return (
    <div className="history-panel">
      <button className="close-btn" onClick={onClose}>×</button>
      <h3>Game History</h3>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="games-list">
          {games.map((game) => (
            <div key={game.id} className="game-item" onClick={() => onLoadGame?.(game.id)}>
              <div className="game-header">
                <span className="date">
                  {new Date(game.start_time).toLocaleDateString()}
                </span>
                <span className="result">{game.result}</span>
              </div>
              <div className="game-details">
                <span>{game.white_player} vs {game.black_player} (ELO: {game.engine_elo})</span>
                <span>{game.total_moves} moves</span>
                {game.opening_name && <span className="opening">{game.opening_name}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// —————————————————————————————————————————————————————————— Main App
export default function App() {
  // —————————————————————————————————————————————————————— State
  const chessRef = useRef(new Chess());
  const [fen, setFen] = useState<string>("");
  const [boardSize, setBoardSize] = useState(() =>
    Math.min(window.innerWidth * 0.9, window.innerHeight * 0.8)
  );
  const [gameOver, setGameOver] = useState(false);
  const [result, setResult] = useState("");
  const [termination, setTermination] = useState("");
  const [isThinking, setThinking] = useState(false);
  const [engineCfg, setEngineCfg] = useState<EngineConfig>({ elo: 1320, time: "0.1" });
  const [error, setError] = useState<string | null>(null);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [moveHistory, setMoveHistory] = useState<string[]>([]);
  const [showMoveHistory, setShowMoveHistory] = useState(false);
  const [hints, setHints] = useState<BestMove[]>([]);
  const [showHints, setShowHints] = useState(false);
  const [lastMove, setLastMove] = useState<string | null>(null);
  const [turn, setTurn] = useState<"white" | "black">("white");

  // Click-to-move helpers
  const [selected, setSelected] = useState<string | null>(null);
  const [targets, setTargets] = useState<string[]>([]);

  // —————————————————————————————————————————————————————— Effects
  useEffect(() => {
    const onResize = () => {
      setBoardSize(Math.min(window.innerWidth * 0.9, window.innerHeight * 0.8));
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // —————————————————————————————————————————————————————— Helpers
  const updateGameState = useCallback((state: GameState) => {
    chessRef.current.load(state.fen);
    setFen(state.fen);
    setTurn(state.turn);
    setMoveHistory(state.moveHistory);
    if (state.lastMove) setLastMove(state.lastMove);
    
    if (state.gameOver) {
      setGameOver(true);
      setResult(state.result || "");
      setTermination(state.termination || "");
    }
  }, []);



  const showError = useCallback((message: string) => {
    setError(message);
    setTimeout(() => setError(null), 5000);
  }, []);

  // —————————————————————————————————————————————————————— API Calls
  const startNewGame = useCallback(async () => {
    console.log("STARTING")
    try {
      setError(null);
      const state = await ChessAPI.initializeBoard(engineCfg.elo, parseFloat(engineCfg.time));
      updateGameState(state);
      console.log(state)
      setGameOver(false);
      setResult("");
      setTermination("");
      setSelected(null);
      setTargets([]);
      setLastMove(null);
      setShowAnalysis(false);
      setAnalysis(null);
    } catch (err) {
      showError("Failed to start new game");
      console.error(err);
    }
  }, [engineCfg, updateGameState, showError]);


 // Fetch top-3 moves as a “hint”
 const requestHints = useCallback(async () => {
   if (!fen) return;
   try {
     const res = await ChessAPI.getBestMoves(3, 0.2);
     setHints(res.best_moves);
     setShowHints(true);
   } catch (err) {
     showError("Could not fetch hints");
   }
 }, [fen, showError]);
 

  const pushPlayerMove = useCallback(async (uci: string): Promise<boolean> => {
    try {
      const state = await ChessAPI.postMove(uci);
      updateGameState(state);
      return true;
    } catch (err) {
      showError(err instanceof Error ? err.message : "Invalid move");
      return false;
    }
  }, [updateGameState, showError]);

  const requestEngineMove = useCallback(async () => {
    try {
      setThinking(true);
      const state = await ChessAPI.engineMove(engineCfg);
      updateGameState(state);
    } catch (err) {
      showError("Engine move failed");
    } finally {
      setThinking(false);
    }
  }, [engineCfg, updateGameState, showError]);

  const requestAnalysis = useCallback(async () => {
    if (!fen) return;
    try {
      const result = await ChessAPI.analyzePosition(fen, 20);
      setAnalysis(result);
      setShowAnalysis(true);
    } catch (err) {
      showError("Analysis failed");
    }
  }, [fen, showError]);

  // —————————————————————————————————————————————————————— Click Handler
  const onSquareClick = useCallback(
    async (square: string) => {
      if (gameOver || isThinking) return;

      // First click - select piece
      if (!selected) {
        const piece = chessRef.current.get(square as Square);
        if (!piece || piece.color !== chessRef.current.turn()) return;

        const moves = chessRef.current.moves({ square: square as Square, verbose: true }) as Move[];
        if (!moves.length) return;

        setSelected(square);
        setTargets(moves.map((m) => m.to));
        return;
      }

      // Click same square - deselect
      if (square === selected) {
        setSelected(null);
        setTargets([]);
        return;
      }

      // Attempt move
      if (targets.includes(square)) {
        let uci = selected + square;
        const moving = chessRef.current.get(selected as Square);
        if (moving?.type === "p" && (square[1] === "8" || square[1] === "1")) {
          uci += "q"; // Auto-promote to queen
        }
        
        const success = await pushPlayerMove(uci);
        if (success) {
          setSelected(null);
          setTargets([]);
          if (!chessRef.current.isGameOver()) {
            await requestEngineMove();
          }
        }
        return;
      }

      // Click another piece
      const piece = chessRef.current.get(square as Square);
      if (piece && piece.color === chessRef.current.turn()) {
        const moves = chessRef.current.moves({ square: square as Square, verbose: true }) as Move[];
        setSelected(square);
        setTargets(moves.map((m) => m.to));
      } else {
        setSelected(null);
        setTargets([]);
      }
    },
    [gameOver, isThinking, selected, targets, pushPlayerMove, requestEngineMove]
  );

  const onPieceDrop = useCallback(
    async (sourceSquare: Square, targetSquare: Square, piece: any): Promise<boolean> => {
      if (gameOver || isThinking) return false;

      let uci = sourceSquare + targetSquare;
      const moving = chessRef.current.get(sourceSquare);
      if (moving?.type === "p" && (targetSquare[1] === "8" || targetSquare[1] === "1")) {
        uci += "q";
      }

      const success = await pushPlayerMove(uci);
      if (success) {
        setSelected(null);
        setTargets([]);
        if (!chessRef.current.isGameOver()) {
          await requestEngineMove();
        }
      }
      return success;
    },
    [gameOver, isThinking, pushPlayerMove, requestEngineMove]
  );
    // Helper function to find king square
    // const findKingSquare = (chess: Chess, color: Color): string | null => {
    //   const board = chess.board();
    //   for (let row = 0; row < 8; row++) {
    //     for (let col = 0; col < 8; col++) {
    //       const piece = board[row][col];
    //       if (piece && piece.type === 'k' && piece.color === color) {
    //         return String.fromCharCode(97 + col) + (8 - row);
    //       }
    //     }
    //   }
    //   return null;
    // };

  // —————————————————————————————————————————————————————— Square Styles
  const squareStyles = useMemo<Record<string, React.CSSProperties>>(() => {
    const styles: Record<string, React.CSSProperties> = {};
    
    // Highlight selected square
    if (selected) {
      styles[selected] = { backgroundColor: SELECT_COLOUR };
    }
    
    // Highlight target squares
    targets.forEach((sq) => {
      styles[sq] = { background: TARGET_COLOUR };
    });
    
    // Highlight last move
    if (lastMove && lastMove.length >= 4) {
      const from = lastMove.substring(0, 2);
      const to = lastMove.substring(2, 4);
      styles[from] = { ...styles[from], backgroundColor: LAST_MOVE_COLOUR };
      styles[to] = { ...styles[to], backgroundColor: LAST_MOVE_COLOUR };
    }
    
    // Highlight king in check
    if (chessRef.current.inCheck()) {
      const kingSquare = findKingSquare(chessRef.current, chessRef.current.turn());
      if (kingSquare) {
        styles[kingSquare] = { ...styles[kingSquare], backgroundColor: CHECK_COLOUR };
      }
    }
    
    return styles;
  }, [selected, targets, lastMove, fen]);



  // —————————————————————————————————————————————————————— Render
  return (
    <div className="app-container">
      {/* Pre-game Setup */}
      {!fen && (
        <div className="setup-screen">
          <h1 className="title">♔ React × Stockfish Chess ♚</h1>
          <div className="setup-card">
            <h2>Configure Your Opponent</h2>
            <div className="config-grid">
              <div className="config-item">
                <label htmlFor="elo">Engine Strength (ELO)</label>
                <input
                  id="elo"
                  type="number"
                  min={800}
                  max={3000}
                  step={50}
                  value={engineCfg.elo}
                  onChange={(e) =>
                    setEngineCfg({ ...engineCfg, elo: parseInt(e.target.value, 10) || 1320 })
                  }
                />
                <span className="hint">800 = Beginner, 2800 = Master</span>
              </div>
              <div className="config-item">
                <label htmlFor="time">Think Time (seconds)</label>
                <input
                  id="time"
                  type="number"
                  min={0.05}
                  max={5}
                  step={0.05}
                  value={engineCfg.time}
                  onChange={(e) =>
                    setEngineCfg({ ...engineCfg, time: e.target.value })
                  }
                />
                <span className="hint">Longer = Stronger moves</span>
              </div>
            </div>
            <button className="start-button" onClick={startNewGame}>
              Start New Game
            </button>
            <button className="history-button" onClick={() => setShowHistory(true)}>
              View Game History
            </button>
          </div>
        </div>
      )}

      {/* Game Board */}
      {fen && (
        <div className="game-container">
          <div className="game-header">
            <div className="player-info">
              <div className={`player ${turn === 'black' ? 'active' : ''}`}>
                <span className="player-name">Stockfish {engineCfg.elo}</span>
                <span className="player-color">●</span>
              </div>
              <div className="game-status">
                {isThinking && <span className="thinking">Thinking...</span>}
                {gameOver && <span className="game-over">{termination}</span>}
              </div>
              <div className={`player ${turn === 'white' ? 'active' : ''}`}>
                <span className="player-color">○</span>
                <span className="player-name">You</span>
              </div>
            </div>
          </div>

          <div className="board-wrapper">
            <Chessboard
              id="main-board"
              position={fen}
              boardWidth={boardSize}
              arePiecesDraggable={!gameOver && !isThinking && turn === 'white'}
              onPieceDrop={(sourceSquare, targetSquare, piece) => {
                onPieceDrop(sourceSquare, targetSquare, piece);
                return false; // Prevent auto-move, let async logic handle it
              }}
              onSquareClick={onSquareClick}
              customSquareStyles={squareStyles}
              boardOrientation="white"
              animationDuration={200}
            />
          </div>

          {/* Control Buttons */}
          <div className="controls">
            <button 
              className="control-btn" 
              onClick={requestAnalysis}
              disabled={gameOver || isThinking}
            >
              Analyze Position
            </button>
      <button 
        className="control-btn" 
        onClick={() => setShowMoveHistory(v => !v)}
      >
        {showMoveHistory ? "Hide" : "Show"} Move History
      </button>
      <button 
        className="control-btn" 
        onClick={requestHints}
        disabled={gameOver || isThinking}
      >
        Hint
      </button>
            <button 
              className="control-btn" 
              onClick={() => setShowHistory(true)}
            >
              Game History
            </button>
            <button 
              className="control-btn primary" 
              onClick={startNewGame}
            >
              New Game
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {/* Game Over Overlay */}
          {gameOver && (
            <div className="game-over-overlay">
              <div className="game-over-content">
                <h2>Game Over</h2>
                <p className="result">{result}</p>
                <p className="termination">{termination}</p>
                <div className="game-over-actions">
                  <button onClick={startNewGame}>Play Again</button>
                  <button onClick={requestAnalysis}>Analyze Game</button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}


  {/* ——————— Move History Sidebar ——————— */}
  {showMoveHistory && (
    <aside className="sidebar move-history">
      <h3>Move History</h3>
      <ol>
        {moveHistory.map((m, i) => (
          <li key={i}>{m}</li>
        ))}
      </ol>
    </aside>
  )}

  {/* ——————— Hint Panel ——————— */}
  {showHints && (
    <aside className="sidebar hint-panel">
      <button className="close-btn" onClick={() => setShowHints(false)}>×</button>
      <h3>Top 3 Moves</h3>
      <ul>
        {hints.map(h => (
          <li key={h.rank}>
            <strong>#{h.rank}:</strong> {h.san}{" "}
            {h.evaluation !== undefined && `(${h.evaluation > 0 ? "+" : ""}${h.evaluation.toFixed(2)})`}
            {h.mate_in !== undefined && ` M${h.mate_in}`}
          </li>
        ))}
      </ul>
    </aside>
  )}

      {/* Analysis Panel */}
      <AnalysisPanel 
        show={showAnalysis} 
        analysis={analysis} 
        onClose={() => setShowAnalysis(false)} 
      />

      {/* Game History Panel */}
      <GameHistoryPanel 
        show={showHistory} 
        onClose={() => setShowHistory(false)}
        onLoadGame={(gameId) => {
          console.log("Load game:", gameId);
          setShowHistory(false);
        }}
      />
    </div>
  );
}