// Google Apps Script để kết nối Streamlit với Google Sheets làm Database

function doGet(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet();
  
  // Đọc hoặc tạo các sheet mặc định nếu chưa có
  var matchesSheet = sheet.getSheetByName("Matches");
  if (!matchesSheet) {
    initSheets();
    matchesSheet = sheet.getSheetByName("Matches");
  }
  
  var matches = getRowsData(matchesSheet);
  var users = getRowsData(sheet.getSheetByName("Users"));
  var predictionsRaw = getRowsData(sheet.getSheetByName("Predictions"));
  
  // Format predictions về dạng { userKey: { matchId: { score1, score2 } } }
  var predictions = {};
  predictionsRaw.forEach(function(row) {
    var key = row.userKey;
    if (!predictions[key]) {
      predictions[key] = {};
    }
    predictions[key][row.matchId] = {
      score1: row.score1 !== "" ? parseInt(row.score1) : null,
      score2: row.score2 !== "" ? parseInt(row.score2) : null
    };
  });
  
  var data = {
    matches: matches,
    users: users,
    predictions: predictions
  };
  
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet();
  var postData = JSON.parse(e.postData.contents);
  var action = postData.action;
  
  if (action === "save_predictions") {
    var userKey = postData.userKey;
    var name = postData.name;
    var unit = postData.unit;
    var preds = postData.predictions; // { matchId: { score1, score2 } }
    
    var usersSheet = sheet.getSheetByName("Users");
    var predsSheet = sheet.getSheetByName("Predictions");
    
    // 1. Đăng ký người dùng nếu chưa có
    var users = getRowsData(usersSheet);
    var userExists = users.some(function(u) {
      return u.name.toLowerCase() === name.toLowerCase() && u.unit.toLowerCase() === unit.toLowerCase();
    });
    
    if (!userExists && name.toLowerCase() !== "admin") {
      usersSheet.appendRow([name, unit, false, 0, 0, 0, 0]);
    }
    
    // 2. Lưu dự đoán, bỏ qua nếu đã có dự đoán từ trước
    var existingPreds = getRowsData(predsSheet);
    var predMap = {};
    existingPreds.forEach(function(p) {
      if (p.userKey === userKey) {
        predMap[p.matchId] = true;
      }
    });
    
    var matchesSheet = sheet.getSheetByName("Matches");
    var matches = getRowsData(matchesSheet);
    
    var nowStr = Utilities.formatDate(new Date(), "GMT+7", "yyyy-MM-dd'T'HH:mm:ss");
    Object.keys(preds).forEach(function(matchId) {
      // Chỉ lưu nếu trận đấu chưa bắt đầu, chưa kết thúc và CHƯA có dự đoán nào trước đó cho trận này
      var match = matches.find(function(m) { return m.id === matchId; });
      if (match && match.status !== "finished" && !predMap[matchId] && nowStr < match.date) {
        var score1 = preds[matchId].score1;
        var score2 = preds[matchId].score2;
        if (score1 !== null && score2 !== null) {
          predsSheet.appendRow([userKey, matchId, score1, score2]);
        }
      }
    });
    
    return ContentService.createTextOutput(JSON.stringify({ success: true }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } else if (action === "admin_update_match") {
    var matchId = postData.matchId;
    var status = postData.status;
    var score1 = postData.score1;
    var score2 = postData.score2;
    
    var matchesSheet = sheet.getSheetByName("Matches");
    var matches = getRowsData(matchesSheet);
    
    var matchRowIdx = -1;
    for (var i = 0; i < matches.length; i++) {
      if (matches[i].id === matchId) {
        matchRowIdx = i + 2; // +2 vì row 1 là header
        break;
      }
    }
    
    if (matchRowIdx !== -1) {
      matchesSheet.getRange(matchRowIdx, 5).setValue(status); // status
      matchesSheet.getRange(matchRowIdx, 6).setValue(score1); // score1
      matchesSheet.getRange(matchRowIdx, 7).setValue(score2); // score2
      
      var outcome = "";
      if (score1 !== null && score2 !== null) {
        outcome = score1 > score2 ? "team1" : (score1 < score2 ? "team2" : "draw");
        matchesSheet.getRange(matchRowIdx, 8).setValue(outcome); // outcome
        
        // Logic tự động thăng hạng (Auto-Advance) cho Knockout
        var matchObj = matches[matchRowIdx - 2];
        var winner = score1 > score2 ? matchObj.team1 : matchObj.team2;
        var loser = score1 > score2 ? matchObj.team2 : matchObj.team1;
        var nextMatchId = matchObj.nextMatchId;
        
        if (nextMatchId) {
          var nextMatchRowIdx = -1;
          for (var j = 0; j < matches.length; j++) {
            if (matches[j].id === nextMatchId) {
              nextMatchRowIdx = j + 2;
              break;
            }
          }
          if (nextMatchRowIdx !== -1) {
            var lastChar = matchId.charAt(matchId.length - 1);
            if (["1", "3", "5", "7"].includes(lastChar)) {
              matchesSheet.getRange(nextMatchRowIdx, 2).setValue(winner); // team1
            } else {
              matchesSheet.getRange(nextMatchRowIdx, 3).setValue(winner); // team2
            }
          }
        }
        
        // Tranh hạng ba
        if (matchId === "sf_1") {
          var thirdRowIdx = getMatchRowIndex(matches, "third");
          if (thirdRowIdx !== -1) matchesSheet.getRange(thirdRowIdx, 2).setValue(loser);
        } else if (matchId === "sf_2") {
          var thirdRowIdx = getMatchRowIndex(matches, "third");
          if (thirdRowIdx !== -1) matchesSheet.getRange(thirdRowIdx, 3).setValue(loser);
        }
      }
      
      // Tính toán lại điểm số
      recalculatePoints(sheet);
      
      return ContentService.createTextOutput(JSON.stringify({ success: true }))
        .setMimeType(ContentService.MimeType.JSON);
    }
  } else if (action === "import_database") {
    var matches = postData.matches;
    var users = postData.users;
    var predictions = postData.predictions;
    
    // Ghi đè Matches sheet
    var matchesSheet = sheet.getSheetByName("Matches");
    if (matchesSheet) {
      matchesSheet.clear();
      matchesSheet.appendRow(["id", "team1", "team2", "date", "status", "score1", "score2", "outcome", "round", "nextMatchId"]);
      matches.forEach(function(m) {
        matchesSheet.appendRow([m.id, m.team1, m.team2, m.date, m.status, m.score1, m.score2, m.outcome, m.round, m.nextMatchId || ""]);
      });
    }
    
    // Ghi đè Users sheet
    var usersSheet = sheet.getSheetByName("Users");
    if (usersSheet) {
      usersSheet.clear();
      usersSheet.appendRow(["name", "unit", "isAdmin", "points", "correctScores", "correctOutcomes", "unpredicted"]);
      users.forEach(function(u) {
        usersSheet.appendRow([u.name, u.unit, u.isAdmin, u.points || 0, u.correctScores || 0, u.correctOutcomes || 0, u.unpredicted || 0]);
      });
    }
    
    // Ghi đè Predictions sheet
    var predsSheet = sheet.getSheetByName("Predictions");
    if (predsSheet) {
      predsSheet.clear();
      predsSheet.appendRow(["userKey", "matchId", "score1", "score2"]);
      Object.keys(predictions).forEach(function(userKey) {
        var userPreds = predictions[userKey];
        Object.keys(userPreds).forEach(function(matchId) {
          var p = userPreds[matchId];
          predsSheet.appendRow([userKey, matchId, p.score1, p.score2]);
        });
      });
    }
    
    return ContentService.createTextOutput(JSON.stringify({ success: true }))
      .setMimeType(ContentService.MimeType.JSON);
  }
  
  return ContentService.createTextOutput(JSON.stringify({ error: "Invalid Action" }))
    .setMimeType(ContentService.MimeType.JSON);
}

function getMatchRowIndex(matches, id) {
  for (var i = 0; i < matches.length; i++) {
    if (matches[i].id === id) return i + 2;
  }
  return -1;
}

// Khởi tạo các Sheet và dữ liệu giải đấu mặc định
function initSheets() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet();
  
  var matchesSheet = getOrCreateSheet(sheet, "Matches");
  var usersSheet = getOrCreateSheet(sheet, "Users");
  var predsSheet = getOrCreateSheet(sheet, "Predictions");
  
  matchesSheet.clear();
  matchesSheet.appendRow(["id", "team1", "team2", "date", "status", "score1", "score2", "outcome", "round", "nextMatchId"]);
  
  usersSheet.clear();
  usersSheet.appendRow(["name", "unit", "isAdmin", "points", "correctScores", "correctOutcomes", "unpredicted"]);
  
  predsSheet.clear();
  predsSheet.appendRow(["userKey", "matchId", "score1", "score2"]);
  
    var DEFAULT_MATCHES = [
    ['m1', 'Mexico', 'Nam Phi', '2026-06-12T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m2', 'Hàn Quốc', 'CH Séc', '2026-06-12T09:00:00', 'pending', '', '', '', 'group', ''],
    ['m3', 'Canada', 'Bosnia', '2026-06-13T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m4', 'Mỹ', 'Paraguay', '2026-06-13T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m5', 'Qatar', 'Thụy Sĩ', '2026-06-14T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m6', 'Brazil', 'Marocco', '2026-06-14T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m7', 'Haiti', 'Scotland', '2026-06-14T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m8', 'Úc', 'Thổ Nhĩ Kỳ', '2026-06-14T11:00:00', 'pending', '', '', '', 'group', ''],
    ['m9', 'Đức', 'Curacao', '2026-06-15T00:00:00', 'pending', '', '', '', 'group', ''],
    ['m10', 'Hà Lan', 'Nhật Bản', '2026-06-15T03:00:00', 'pending', '', '', '', 'group', ''],
    ['m11', 'Bờ Biển Ngà', 'Ecuador', '2026-06-15T06:00:00', 'pending', '', '', '', 'group', ''],
    ['m12', 'Thụy Điển', 'Tunisia', '2026-06-15T09:00:00', 'pending', '', '', '', 'group', ''],
    ['m13', 'Tây Ban Nha', 'Cabo Verde', '2026-06-15T23:00:00', 'pending', '', '', '', 'group', ''],
    ['m14', 'Bỉ', 'Ai Cập', '2026-06-16T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m15', 'Saudi Arabia', 'Uruguay', '2026-06-16T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m16', 'Iran', 'New Zealand', '2026-06-16T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m17', 'Pháp', 'Senegal', '2026-06-17T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m18', 'Iraq', 'Na Uy', '2026-06-17T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m19', 'Argentina', 'Algeria', '2026-06-17T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m20', 'Áo', 'Jordan', '2026-06-17T11:00:00', 'pending', '', '', '', 'group', ''],
    ['m21', 'Bồ Đào Nha', 'CHDC Congo', '2026-06-18T00:00:00', 'pending', '', '', '', 'group', ''],
    ['m22', 'Anh', 'Croatia', '2026-06-18T03:00:00', 'pending', '', '', '', 'group', ''],
    ['m23', 'Ghana', 'Panama', '2026-06-18T06:00:00', 'pending', '', '', '', 'group', ''],
    ['m24', 'Uzbekistan', 'Colombia', '2026-06-18T09:00:00', 'pending', '', '', '', 'group', ''],
    ['m25', 'CH Séc', 'Nam Phi', '2026-06-18T23:00:00', 'pending', '', '', '', 'group', ''],
    ['m26', 'Thụy Sĩ', 'Bosnia', '2026-06-19T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m27', 'Canada', 'Qatar', '2026-06-19T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m28', 'Mexico', 'Hàn Quốc', '2026-06-19T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m29', 'Mỹ', 'Úc', '2026-06-20T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m30', 'Scotland', 'Marocco', '2026-06-20T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m31', 'Brazil', 'Haiti', '2026-06-20T07:30:00', 'pending', '', '', '', 'group', ''],
    ['m32', 'Thổ Nhĩ Kỳ', 'Paraguay', '2026-06-20T10:00:00', 'pending', '', '', '', 'group', ''],
    ['m33', 'Hà Lan', 'Thụy Điển', '2026-06-21T00:00:00', 'pending', '', '', '', 'group', ''],
    ['m34', 'Đức', 'Bờ Biển Ngà', '2026-06-21T03:00:00', 'pending', '', '', '', 'group', ''],
    ['m35', 'Ecuador', 'Curacao', '2026-06-21T07:00:00', 'pending', '', '', '', 'group', ''],
    ['m36', 'Tunisia', 'Nhật Bản', '2026-06-21T11:00:00', 'pending', '', '', '', 'group', ''],
    ['m37', 'Tây Ban Nha', 'Saudi Arabia', '2026-06-21T23:00:00', 'pending', '', '', '', 'group', ''],
    ['m38', 'Bỉ', 'Iran', '2026-06-22T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m39', 'Uruguay', 'Cabo Verde', '2026-06-22T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m40', 'New Zealand', 'Ai Cập', '2026-06-22T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m41', 'Argentina', 'Áo', '2026-06-23T00:00:00', 'pending', '', '', '', 'group', ''],
    ['m42', 'Pháp', 'Iraq', '2026-06-23T04:00:00', 'pending', '', '', '', 'group', ''],
    ['m43', 'Na Uy', 'Senegal', '2026-06-23T07:00:00', 'pending', '', '', '', 'group', ''],
    ['m44', 'Jordan', 'Algeria', '2026-06-23T10:00:00', 'pending', '', '', '', 'group', ''],
    ['m45', 'Bồ Đào Nha', 'Uzbekistan', '2026-06-24T00:00:00', 'pending', '', '', '', 'group', ''],
    ['m46', 'Anh', 'Ghana', '2026-06-24T03:00:00', 'pending', '', '', '', 'group', ''],
    ['m47', 'Panama', 'Croatia', '2026-06-24T06:00:00', 'pending', '', '', '', 'group', ''],
    ['m48', 'Colombia', 'CHDC Congo', '2026-06-24T09:00:00', 'pending', '', '', '', 'group', ''],
    ['m49', 'Bosnia', 'Qatar', '2026-06-25T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m50', 'Thụy Sĩ', 'Canada', '2026-06-25T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m51', 'Marocco', 'Haiti', '2026-06-25T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m52', 'Scotland', 'Brazil', '2026-06-25T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m53', 'Nam Phi', 'Hàn Quốc', '2026-06-25T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m54', 'CH Séc', 'Mexico', '2026-06-25T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m55', 'Curacao', 'Bờ Biển Ngà', '2026-06-26T03:00:00', 'pending', '', '', '', 'group', ''],
    ['m56', 'Ecuador', 'Đức', '2026-06-26T03:00:00', 'pending', '', '', '', 'group', ''],
    ['m57', 'Tunisia', 'Hà Lan', '2026-06-26T06:00:00', 'pending', '', '', '', 'group', ''],
    ['m58', 'Nhật Bản', 'Thụy Điển', '2026-06-26T06:00:00', 'pending', '', '', '', 'group', ''],
    ['m59', 'Thổ Nhĩ Kỳ', 'Mỹ', '2026-06-26T09:00:00', 'pending', '', '', '', 'group', ''],
    ['m60', 'Paraguay', 'Úc', '2026-06-26T09:00:00', 'pending', '', '', '', 'group', ''],
    ['m61', 'Na Uy', 'Pháp', '2026-06-27T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m62', 'Senegal', 'Iraq', '2026-06-27T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m63', 'Cabo Verde', 'Saudi Arabia', '2026-06-27T07:00:00', 'pending', '', '', '', 'group', ''],
    ['m64', 'Uruguay', 'Tây Ban Nha', '2026-06-27T07:00:00', 'pending', '', '', '', 'group', ''],
    ['m65', 'New Zealand', 'Bỉ', '2026-06-27T10:00:00', 'pending', '', '', '', 'group', ''],
    ['m66', 'Ai Cập', 'Iran', '2026-06-27T10:00:00', 'pending', '', '', '', 'group', ''],
    ['m67', 'Panama', 'Anh', '2026-06-28T04:00:00', 'pending', '', '', '', 'group', ''],
    ['m68', 'Croatia', 'Ghana', '2026-06-28T04:00:00', 'pending', '', '', '', 'group', ''],
    ['m69', 'Colombia', 'Bồ Đào Nha', '2026-06-28T06:30:00', 'pending', '', '', '', 'group', ''],
    ['m70', 'CHDC Congo', 'Uzbekistan', '2026-06-28T06:30:00', 'pending', '', '', '', 'group', ''],
    ['m71', 'Algeria', 'Áo', '2026-06-28T09:00:00', 'pending', '', '', '', 'group', ''],
    ['m72', 'Jordan', 'Argentina', '2026-06-28T09:00:00', 'pending', '', '', '', 'group', ''],
    ['r32_1', 'Á quân Bảng A', 'Á quân Bảng B', '2026-06-29T02:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_4', 'Nhất Bảng C', 'Á quân Bảng F', '2026-06-30T00:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_2', 'Nhất Bảng E', 'Hạng 3 A/B/C/D/F', '2026-06-30T03:30:00', 'pending', '', '', '', 'r32', ''],
    ['r32_3', 'Nhất Bảng F', 'Á quân Bảng C', '2026-06-30T08:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_6', 'Á quân Bảng E', 'Á quân Bảng I', '2026-07-01T00:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_5', 'Nhất Bảng I', 'Hạng 3 C/D/F/G/H', '2026-07-01T04:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_7', 'Nhất Bảng A', 'Hạng 3 C/E/F/H/I', '2026-07-01T08:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_8', 'Nhất Bảng L', 'Hạng 3 E/H/I/J/K', '2026-07-01T23:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_11', 'Nhất Bảng G', 'Hạng 3 A/E/H/I/J', '2026-07-02T03:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_10', 'Nhất Bảng D', 'Hạng 3 B/E/F/I/J', '2026-07-02T07:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_12', 'Nhất Bảng H', 'Á quân Bảng J', '2026-07-03T02:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_9', 'Á quân Bảng K', 'Á quân Bảng L', '2026-07-03T06:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_13', 'Nhất Bảng B', 'Hạng 3 E/F/G/I/J', '2026-07-03T10:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_16', 'Á quân Bảng D', 'Á quân Bảng G', '2026-07-04T01:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_14', 'Nhất Bảng J', 'Á quân Bảng H', '2026-07-04T05:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_15', 'Nhất Bảng K', 'Hạng 3 D/E/I/J/L', '2026-07-04T08:30:00', 'pending', '', '', '', 'r32', ''],
    ['r16_2', 'Thắng 73', 'Thắng 75', '2026-07-05T00:00:00', 'pending', '', '', '', 'r16', ''],
    ['r16_1', 'Thắng 74', 'Thắng 77', '2026-07-05T04:00:00', 'pending', '', '', '', 'r16', ''],
    ['r16_3', 'Thắng 76', 'Thắng 78', '2026-07-06T03:00:00', 'pending', '', '', '', 'r16', ''],
    ['r16_4', 'Thắng 79', 'Thắng 80', '2026-07-06T07:00:00', 'pending', '', '', '', 'r16', ''],
    ['r16_5', 'Thắng 83', 'Thắng 84', '2026-07-07T02:00:00', 'pending', '', '', '', 'r16', ''],
    ['r16_6', 'Thắng 81', 'Thắng 82', '2026-07-07T07:00:00', 'pending', '', '', '', 'r16', ''],
    ['r16_7', 'Thắng 86', 'Thắng 88', '2026-07-07T23:00:00', 'pending', '', '', '', 'r16', ''],
    ['r16_8', 'Thắng 85', 'Thắng 87', '2026-07-08T03:00:00', 'pending', '', '', '', 'r16', ''],
    ['qf_1', 'Thắng 89', 'Thắng 90', '2026-07-10T03:00:00', 'pending', '', '', '', 'qf', ''],
    ['qf_2', 'Thắng 93', 'Thắng 94', '2026-07-11T02:00:00', 'pending', '', '', '', 'qf', ''],
    ['qf_3', 'Thắng 91', 'Thắng 92', '2026-07-12T04:00:00', 'pending', '', '', '', 'qf', ''],
    ['qf_4', 'Thắng 95', 'Thắng 96', '2026-07-12T08:00:00', 'pending', '', '', '', 'qf', ''],
    ['sf_1', 'Thắng 97', 'Thắng 98', '2026-07-15T02:00:00', 'pending', '', '', '', 'sf', ''],
    ['sf_2', 'Thắng 99', 'Thắng 100', '2026-07-16T02:00:00', 'pending', '', '', '', 'sf', ''],
    ['third', 'Thua 101', 'Thua 102', '2026-07-19T04:00:00', 'pending', '', '', '', 'third', ''],
    ['final', 'Thắng 101', 'Thắng 102', '2026-07-20T02:00:00', 'pending', '', '', '', 'final', ''],
  ];
  
  for (var i = 0; i < DEFAULT_MATCHES.length; i++) {
    matchesSheet.appendRow(DEFAULT_MATCHES[i]);
  }
}

function getOrCreateSheet(sheet, name) {
  var s = sheet.getSheetByName(name);
  if (!s) s = sheet.insertSheet(name);
  return s;
}

function getRowsData(sheet) {
  var rows = sheet.getDataRange().getValues();
  if (rows.length <= 1) return [];
  var headers = rows[0];
  var data = [];
  for (var i = 1; i < rows.length; i++) {
    var row = rows[i];
    var obj = {};
    for (var j = 0; j < headers.length; j++) {
      var val = row[j];
      if (val === "true" || val === true) val = true;
      if (val === "false" || val === false) val = false;
      obj[headers[j]] = val;
    }
    data.push(obj);
  }
  return data;
}

function recalculatePoints(sheet) {
  var usersSheet = sheet.getSheetByName("Users");
  var matchesSheet = sheet.getSheetByName("Matches");
  var predsSheet = sheet.getSheetByName("Predictions");
  
  var users = getRowsData(usersSheet);
  var matches = getRowsData(matchesSheet);
  var predictions = getRowsData(predsSheet);
  
  // Tạo map reset điểm
  var userMap = {};
  users.forEach(function(u) {
    u.points = 0;
    u.correctScores = 0;
    u.correctOutcomes = 0;
    u.unpredicted = 0;
    userMap[u.name + "-" + u.unit] = u;
  });
  
  // Format predictions về dạng { userKey: { matchId: { score1, score2 } } }
  var predMap = {};
  predictions.forEach(function(p) {
    var key = p.userKey;
    if (!predMap[key]) {
      predMap[key] = {};
    }
    predMap[key][p.matchId] = {
      score1: p.score1,
      score2: p.score2
    };
  });
  
  matches.forEach(function(match) {
    if (match.status !== "finished") return;
    var act1 = parseInt(match.score1);
    var act2 = parseInt(match.score2);
    if (isNaN(act1) || isNaN(act2)) return;
    
    // Duyệt qua tất cả người dùng
    users.forEach(function(u) {
      if (u.name.toLowerCase() === "admin") return;
      var userKey = u.name + "-" + u.unit;
      var userPreds = predMap[userKey] || {};
      var pred = userPreds[match.id];
      
      var user = userMap[userKey];
      if (!user) return;
      
      if (pred) {
        var p1 = parseInt(pred.score1);
        var p2 = parseInt(pred.score2);
        if (!isNaN(p1) && !isNaN(p2)) {
          if (p1 === act1 && p2 === act2) {
            user.points += 0;
            user.correctScores += 1;
          } else {
            user.points -= 1;
            user.correctOutcomes += 1;
          }
          return;
        }
      }
      
      // Không dự đoán -> Phạt -1đ và cộng vào unpredicted
      user.points -= 1;
      user.unpredicted += 1;
    });
  });
  
  // Ghi lại điểm
  var dataRange = usersSheet.getDataRange();
  var values = dataRange.getValues();
  for (var i = 1; i < values.length; i++) {
    var name = values[i][0];
    var unit = values[i][1];
    var user = userMap[name + "-" + unit];
    if (user) {
      usersSheet.getRange(i + 1, 4).setValue(user.points);
      usersSheet.getRange(i + 1, 5).setValue(user.correctScores);
      usersSheet.getRange(i + 1, 6).setValue(user.correctOutcomes);
      usersSheet.getRange(i + 1, 7).setValue(user.unpredicted);
    }
  }
}

// Hàm cập nhật 104 trận đấu World Cup 2026 mà KHÔNG làm mất thông tin Users và Predictions
function updateMatchesOnly() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet();
  var matchesSheet = getOrCreateSheet(sheet, "Matches");
  
  // 1. Sao lưu tỷ số các trận đã kết thúc để không bị mất kết quả khi ghi đè
  var oldMatches = getRowsData(matchesSheet);
  var oldScoresMap = {};
  oldMatches.forEach(function(m) {
    if (m.status === "finished") {
      oldScoresMap[m.id] = {
        status: m.status,
        score1: m.score1,
        score2: m.score2,
        outcome: m.outcome
      };
    }
  });
  
  // 2. Xóa và khởi tạo lại tiêu đề bảng Matches
  matchesSheet.clear();
  matchesSheet.appendRow(["id", "team1", "team2", "date", "status", "score1", "score2", "outcome", "round", "nextMatchId"]);
  
  var DEFAULT_MATCHES = [
    ['m1', 'Mexico', 'Nam Phi', '2026-06-12T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m2', 'Hàn Quốc', 'CH Séc', '2026-06-12T09:00:00', 'pending', '', '', '', 'group', ''],
    ['m3', 'Canada', 'Bosnia', '2026-06-13T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m4', 'Mỹ', 'Paraguay', '2026-06-13T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m5', 'Qatar', 'Thụy Sĩ', '2026-06-14T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m6', 'Brazil', 'Marocco', '2026-06-14T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m7', 'Haiti', 'Scotland', '2026-06-14T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m8', 'Úc', 'Thổ Nhĩ Kỳ', '2026-06-14T11:00:00', 'pending', '', '', '', 'group', ''],
    ['m9', 'Đức', 'Curacao', '2026-06-15T00:00:00', 'pending', '', '', '', 'group', ''],
    ['m10', 'Hà Lan', 'Nhật Bản', '2026-06-15T03:00:00', 'pending', '', '', '', 'group', ''],
    ['m11', 'Bờ Biển Ngà', 'Ecuador', '2026-06-15T06:00:00', 'pending', '', '', '', 'group', ''],
    ['m12', 'Thụy Điển', 'Tunisia', '2026-06-15T09:00:00', 'pending', '', '', '', 'group', ''],
    ['m13', 'Tây Ban Nha', 'Cabo Verde', '2026-06-15T23:00:00', 'pending', '', '', '', 'group', ''],
    ['m14', 'Bỉ', 'Ai Cập', '2026-06-16T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m15', 'Saudi Arabia', 'Uruguay', '2026-06-16T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m16', 'Iran', 'New Zealand', '2026-06-16T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m17', 'Pháp', 'Senegal', '2026-06-17T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m18', 'Iraq', 'Na Uy', '2026-06-17T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m19', 'Argentina', 'Algeria', '2026-06-17T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m20', 'Áo', 'Jordan', '2026-06-17T11:00:00', 'pending', '', '', '', 'group', ''],
    ['m21', 'Bồ Đào Nha', 'CHDC Congo', '2026-06-18T00:00:00', 'pending', '', '', '', 'group', ''],
    ['m22', 'Anh', 'Croatia', '2026-06-18T03:00:00', 'pending', '', '', '', 'group', ''],
    ['m23', 'Ghana', 'Panama', '2026-06-18T06:00:00', 'pending', '', '', '', 'group', ''],
    ['m24', 'Uzbekistan', 'Colombia', '2026-06-18T09:00:00', 'pending', '', '', '', 'group', ''],
    ['m25', 'CH Séc', 'Nam Phi', '2026-06-18T23:00:00', 'pending', '', '', '', 'group', ''],
    ['m26', 'Thụy Sĩ', 'Bosnia', '2026-06-19T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m27', 'Canada', 'Qatar', '2026-06-19T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m28', 'Mexico', 'Hàn Quốc', '2026-06-19T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m29', 'Mỹ', 'Úc', '2026-06-20T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m30', 'Scotland', 'Marocco', '2026-06-20T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m31', 'Brazil', 'Haiti', '2026-06-20T07:30:00', 'pending', '', '', '', 'group', ''],
    ['m32', 'Thổ Nhĩ Kỳ', 'Paraguay', '2026-06-20T10:00:00', 'pending', '', '', '', 'group', ''],
    ['m33', 'Hà Lan', 'Thụy Điển', '2026-06-21T00:00:00', 'pending', '', '', '', 'group', ''],
    ['m34', 'Đức', 'Bờ Biển Ngà', '2026-06-21T03:00:00', 'pending', '', '', '', 'group', ''],
    ['m35', 'Ecuador', 'Curacao', '2026-06-21T07:00:00', 'pending', '', '', '', 'group', ''],
    ['m36', 'Tunisia', 'Nhật Bản', '2026-06-21T11:00:00', 'pending', '', '', '', 'group', ''],
    ['m37', 'Tây Ban Nha', 'Saudi Arabia', '2026-06-21T23:00:00', 'pending', '', '', '', 'group', ''],
    ['m38', 'Bỉ', 'Iran', '2026-06-22T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m39', 'Uruguay', 'Cabo Verde', '2026-06-22T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m40', 'New Zealand', 'Ai Cập', '2026-06-22T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m41', 'Argentina', 'Áo', '2026-06-23T00:00:00', 'pending', '', '', '', 'group', ''],
    ['m42', 'Pháp', 'Iraq', '2026-06-23T04:00:00', 'pending', '', '', '', 'group', ''],
    ['m43', 'Na Uy', 'Senegal', '2026-06-23T07:00:00', 'pending', '', '', '', 'group', ''],
    ['m44', 'Jordan', 'Algeria', '2026-06-23T10:00:00', 'pending', '', '', '', 'group', ''],
    ['m45', 'Bồ Đào Nha', 'Uzbekistan', '2026-06-24T00:00:00', 'pending', '', '', '', 'group', ''],
    ['m46', 'Anh', 'Ghana', '2026-06-24T03:00:00', 'pending', '', '', '', 'group', ''],
    ['m47', 'Panama', 'Croatia', '2026-06-24T06:00:00', 'pending', '', '', '', 'group', ''],
    ['m48', 'Colombia', 'CHDC Congo', '2026-06-24T09:00:00', 'pending', '', '', '', 'group', ''],
    ['m49', 'Bosnia', 'Qatar', '2026-06-25T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m50', 'Thụy Sĩ', 'Canada', '2026-06-25T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m51', 'Marocco', 'Haiti', '2026-06-25T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m52', 'Scotland', 'Brazil', '2026-06-25T05:00:00', 'pending', '', '', '', 'group', ''],
    ['m53', 'Nam Phi', 'Hàn Quốc', '2026-06-25T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m54', 'CH Séc', 'Mexico', '2026-06-25T08:00:00', 'pending', '', '', '', 'group', ''],
    ['m55', 'Curacao', 'Bờ Biển Ngà', '2026-06-26T03:00:00', 'pending', '', '', '', 'group', ''],
    ['m56', 'Ecuador', 'Đức', '2026-06-26T03:00:00', 'pending', '', '', '', 'group', ''],
    ['m57', 'Tunisia', 'Hà Lan', '2026-06-26T06:00:00', 'pending', '', '', '', 'group', ''],
    ['m58', 'Nhật Bản', 'Thụy Điển', '2026-06-26T06:00:00', 'pending', '', '', '', 'group', ''],
    ['m59', 'Thổ Nhĩ Kỳ', 'Mỹ', '2026-06-26T09:00:00', 'pending', '', '', '', 'group', ''],
    ['m60', 'Paraguay', 'Úc', '2026-06-26T09:00:00', 'pending', '', '', '', 'group', ''],
    ['m61', 'Na Uy', 'Pháp', '2026-06-27T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m62', 'Senegal', 'Iraq', '2026-06-27T02:00:00', 'pending', '', '', '', 'group', ''],
    ['m63', 'Cabo Verde', 'Saudi Arabia', '2026-06-27T07:00:00', 'pending', '', '', '', 'group', ''],
    ['m64', 'Uruguay', 'Tây Ban Nha', '2026-06-27T07:00:00', 'pending', '', '', '', 'group', ''],
    ['m65', 'New Zealand', 'Bỉ', '2026-06-27T10:00:00', 'pending', '', '', '', 'group', ''],
    ['m66', 'Ai Cập', 'Iran', '2026-06-27T10:00:00', 'pending', '', '', '', 'group', ''],
    ['m67', 'Panama', 'Anh', '2026-06-28T04:00:00', 'pending', '', '', '', 'group', ''],
    ['m68', 'Croatia', 'Ghana', '2026-06-28T04:00:00', 'pending', '', '', '', 'group', ''],
    ['m69', 'Colombia', 'Bồ Đào Nha', '2026-06-28T06:30:00', 'pending', '', '', '', 'group', ''],
    ['m70', 'CHDC Congo', 'Uzbekistan', '2026-06-28T06:30:00', 'pending', '', '', '', 'group', ''],
    ['m71', 'Algeria', 'Áo', '2026-06-28T09:00:00', 'pending', '', '', '', 'group', ''],
    ['m72', 'Jordan', 'Argentina', '2026-06-28T09:00:00', 'pending', '', '', '', 'group', ''],
    ['r32_1', 'Á quân Bảng A', 'Á quân Bảng B', '2026-06-29T02:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_4', 'Nhất Bảng C', 'Á quân Bảng F', '2026-06-30T00:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_2', 'Nhất Bảng E', 'Hạng 3 A/B/C/D/F', '2026-06-30T03:30:00', 'pending', '', '', '', 'r32', ''],
    ['r32_3', 'Nhất Bảng F', 'Á quân Bảng C', '2026-06-30T08:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_6', 'Á quân Bảng E', 'Á quân Bảng I', '2026-07-01T00:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_5', 'Nhất Bảng I', 'Hạng 3 C/D/F/G/H', '2026-07-01T04:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_7', 'Nhất Bảng A', 'Hạng 3 C/E/F/H/I', '2026-07-01T08:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_8', 'Nhất Bảng L', 'Hạng 3 E/H/I/J/K', '2026-07-01T23:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_11', 'Nhất Bảng G', 'Hạng 3 A/E/H/I/J', '2026-07-02T03:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_10', 'Nhất Bảng D', 'Hạng 3 B/E/F/I/J', '2026-07-02T07:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_12', 'Nhất Bảng H', 'Á quân Bảng J', '2026-07-03T02:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_9', 'Á quân Bảng K', 'Á quân Bảng L', '2026-07-03T06:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_13', 'Nhất Bảng B', 'Hạng 3 E/F/G/I/J', '2026-07-03T10:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_16', 'Á quân Bảng D', 'Á quân Bảng G', '2026-07-04T01:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_14', 'Nhất Bảng J', 'Á quân Bảng H', '2026-07-04T05:00:00', 'pending', '', '', '', 'r32', ''],
    ['r32_15', 'Nhất Bảng K', 'Hạng 3 D/E/I/J/L', '2026-07-04T08:30:00', 'pending', '', '', '', 'r32', ''],
    ['r16_2', 'Thắng 73', 'Thắng 75', '2026-07-05T00:00:00', 'pending', '', '', '', 'r16', ''],
    ['r16_1', 'Thắng 74', 'Thắng 77', '2026-07-05T04:00:00', 'pending', '', '', '', 'r16', ''],
    ['r16_3', 'Thắng 76', 'Thắng 78', '2026-07-06T03:00:00', 'pending', '', '', '', 'r16', ''],
    ['r16_4', 'Thắng 79', 'Thắng 80', '2026-07-06T07:00:00', 'pending', '', '', '', 'r16', ''],
    ['r16_5', 'Thắng 83', 'Thắng 84', '2026-07-07T02:00:00', 'pending', '', '', '', 'r16', ''],
    ['r16_6', 'Thắng 81', 'Thắng 82', '2026-07-07T07:00:00', 'pending', '', '', '', 'r16', ''],
    ['r16_7', 'Thắng 86', 'Thắng 88', '2026-07-07T23:00:00', 'pending', '', '', '', 'r16', ''],
    ['r16_8', 'Thắng 85', 'Thắng 87', '2026-07-08T03:00:00', 'pending', '', '', '', 'r16', ''],
    ['qf_1', 'Thắng 89', 'Thắng 90', '2026-07-10T03:00:00', 'pending', '', '', '', 'qf', ''],
    ['qf_2', 'Thắng 93', 'Thắng 94', '2026-07-11T02:00:00', 'pending', '', '', '', 'qf', ''],
    ['qf_3', 'Thắng 91', 'Thắng 92', '2026-07-12T04:00:00', 'pending', '', '', '', 'qf', ''],
    ['qf_4', 'Thắng 95', 'Thắng 96', '2026-07-12T08:00:00', 'pending', '', '', '', 'qf', ''],
    ['sf_1', 'Thắng 97', 'Thắng 98', '2026-07-15T02:00:00', 'pending', '', '', '', 'sf', ''],
    ['sf_2', 'Thắng 99', 'Thắng 100', '2026-07-16T02:00:00', 'pending', '', '', '', 'sf', ''],
    ['third', 'Thua 101', 'Thua 102', '2026-07-19T04:00:00', 'pending', '', '', '', 'third', ''],
    ['final', 'Thắng 101', 'Thắng 102', '2026-07-20T02:00:00', 'pending', '', '', '', 'final', ''],
  ];
  
  // 3. Ghi đè danh sách trận đấu và hồi phục tỷ số cũ nếu có
  for (var i = 0; i < DEFAULT_MATCHES.length; i++) {
    var matchRow = DEFAULT_MATCHES[i];
    var mId = matchRow[0];
    if (oldScoresMap[mId]) {
      matchRow[4] = oldScoresMap[mId].status;  // status
      matchRow[5] = oldScoresMap[mId].score1;  // score1
      matchRow[6] = oldScoresMap[mId].score2;  // score2
      matchRow[7] = oldScoresMap[mId].outcome; // outcome
    }
    matchesSheet.appendRow(matchRow);
  }
  
  // 4. Tính toán lại điểm số dựa trên kết quả cũ
  recalculatePoints(sheet);
}

// Hàm tự động cào và cập nhật kết quả từ 24h.com.vn vào Google Sheets
function normalizeName(name) {
  if (!name) return "";
  return name.toLowerCase().replace(/[^a-z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/g, "");
}

// Hàm tự động cào và cập nhật kết quả từ 24h.com.vn vào Google Sheets
function syncResultsFrom24h() {
  var url = 'https://www.24h.com.vn/world-cup-2026/ket-qua-thi-dau-bong-da-world-cup-2026-moi-nhat-c860a1747405.html';
  try {
    var response = UrlFetchApp.fetch(url, {
      "headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      },
      "muteHttpExceptions": true
    });
    
    if (response.getResponseCode() !== 200) {
      Logger.log("Lỗi fetch URL: " + response.getResponseCode());
      return "Lỗi kết nối tới 24h.com.vn (HTTP " + response.getResponseCode() + ")";
    }
    
    var html = response.getContentText("UTF-8");
    var parts = html.split('class="box-items');
    if (parts.length < 2) {
      Logger.log("Không tìm thấy trận đấu nào trên trang 24h.com.vn.");
      return "Không tìm thấy trận đấu nào trên trang 24h.com.vn.";
    }
    
    var parsedMatches = [];
    for (var i = 1; i < parts.length; i++) {
      var part = parts[i];
      var teamRegex = /class="[^"]*?team-name[^"]*?"[^>]*?>([\s\S]*?)<\/span>/g;
      var t1 = "";
      var t2 = "";
      var m1 = teamRegex.exec(part);
      if (m1) t1 = m1[1].replace(/<[^>]*>/g, "").trim();
      var m2 = teamRegex.exec(part);
      if (m2) t2 = m2[1].replace(/<[^>]*>/g, "").trim();
      
      var scoreMatch = part.match(/class="box-score"[\s\S]*?class="box-t[\s\S]*?>([\s\S]*?)<\/div>/);
      var scoreStr = "";
      if (scoreMatch) {
        scoreStr = scoreMatch[1].replace(/<[^>]*>/g, "").trim();
      }
      
      if (t1 && t2) {
        parsedMatches.push({
          team1: t1,
          team2: t2,
          scoreStr: scoreStr
        });
      }
    }
    
    var sheet = SpreadsheetApp.getActiveSpreadsheet();
    var matchesSheet = sheet.getSheetByName("Matches");
    var matches = getRowsData(matchesSheet);
    
    var updated = false;
    var updateMsgs = [];
    
    for (var idx = 0; idx < matches.length; idx++) {
      var m = matches[idx];
      if (m.status === "pending") {
        var db_t1_norm = normalizeName(m.team1);
        var db_t2_norm = normalizeName(m.team2);
        
        var matchFound = null;
        for (var j = 0; j < parsedMatches.length; j++) {
          var w_t1_norm = normalizeName(parsedMatches[j].team1);
          var w_t2_norm = normalizeName(parsedMatches[j].team2);
          
          if ((db_t1_norm === w_t1_norm || w_t1_norm.indexOf(db_t1_norm) !== -1 || db_t1_norm.indexOf(w_t1_norm) !== -1) &&
              (db_t2_norm === w_t2_norm || w_t2_norm.indexOf(db_t2_norm) !== -1 || db_t2_norm.indexOf(w_t2_norm) !== -1)) {
            matchFound = parsedMatches[j];
            break;
          }
        }
        
        if (matchFound) {
          var scoreStr = matchFound.scoreStr;
          // Chỉ lấy tỷ số 90 phút chính thức, bỏ phần hiệp phụ/pen trong ngoặc đơn
          if (scoreStr.indexOf('(') !== -1) {
            scoreStr = scoreStr.split('(')[0].trim();
          }
          if (scoreStr.indexOf('-') !== -1 && scoreStr.length > 1) {
            var scoreParts = scoreStr.split('-');
            var s1Str = scoreParts[0].trim();
            var s2Str = scoreParts[1].trim();
            
            if (s1Str !== "" && s2Str !== "") {
              var s1 = parseInt(s1Str);
              var s2 = parseInt(s2Str);
              
              if (!isNaN(s1) && !isNaN(s2)) {
                var matchRowIdx = idx + 2; // +2 vì row 1 là header
                
                matchesSheet.getRange(matchRowIdx, 5).setValue("finished"); // status
                matchesSheet.getRange(matchRowIdx, 6).setValue(s1);         // score1
                matchesSheet.getRange(matchRowIdx, 7).setValue(s2);         // score2
                
                var outcome = s1 > s2 ? "team1" : (s1 < s2 ? "team2" : "draw");
                matchesSheet.getRange(matchRowIdx, 8).setValue(outcome);    // outcome
                
                // Cập nhật đội đi tiếp (Knockout)
                var winner = s1 > s2 ? m.team1 : m.team2;
                var loser = s1 > s2 ? m.team2 : m.team1;
                var nextMatchId = m.nextMatchId;
                
                if (nextMatchId) {
                  var nextMatchRowIdx = getMatchRowIndex(matches, nextMatchId);
                  if (nextMatchRowIdx !== -1) {
                    var lastChar = m.id.charAt(m.id.length - 1);
                    if (["1", "3", "5", "7", "9"].includes(lastChar)) {
                      matchesSheet.getRange(nextMatchRowIdx, 2).setValue(winner); // team1
                    } else {
                      matchesSheet.getRange(nextMatchRowIdx, 3).setValue(winner); // team2
                    }
                  }
                }
                
                // Tranh hạng ba
                if (m.id === "sf_1") {
                  var thirdRowIdx = getMatchRowIndex(matches, "third");
                  if (thirdRowIdx !== -1) matchesSheet.getRange(thirdRowIdx, 2).setValue(loser);
                } else if (m.id === "sf_2") {
                  var thirdRowIdx = getMatchRowIndex(matches, "third");
                  if (thirdRowIdx !== -1) matchesSheet.getRange(thirdRowIdx, 3).setValue(loser);
                }
                
                updated = true;
                updateMsgs.push(m.team1 + " " + s1 + "-" + s2 + " " + m.team2);
              }
            }
          }
        }
      }
    }
    
    if (updated) {
      recalculatePoints(sheet);
      return "Đồng bộ thành công: " + updateMsgs.join(", ");
    }
    
    return "Không có kết quả mới nào cần cập nhật.";
  } catch (e) {
    Logger.log("Lỗi đồng bộ: " + e.toString());
    return "Lỗi đồng bộ: " + e.toString();
  }
}


// Tạo trigger chạy ngầm tự động mỗi 15 phút
function createAutoSyncTrigger() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === "syncResultsFrom24h") {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
  
  ScriptApp.newTrigger("syncResultsFrom24h")
    .timeBased()
    .everyMinutes(15)
    .create();
    
  Logger.log("Đã đăng ký trigger chạy ngầm syncResultsFrom24h tự động mỗi 15 phút.");
}
