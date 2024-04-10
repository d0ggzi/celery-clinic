function handleClick(doctor) {
  fetch('/records', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ doctor: doctor }),
  })
  .then(response => response.json())
  .then(data => {
    getStatus(data.record_id)
  })
}

function getStatus(record_id) {
  fetch(`/records/${record_id}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    },
  })
  .then(response => response.json())
  .then(res => {
    // console.log(res);
    const taskStatus = res.record_status;

    var row = document.getElementById(record_id);
    // если строчка уже есть в таблице, просто обновить ее
    if (row !== null){
      row.getElementsByTagName('td')[2].innerHTML = taskStatus;
      row.getElementsByTagName('td')[1].innerHTML = res.doctor;
    } else {
      // если строчки еще нет в таблице, добавить новую
      const html = `
      <tr id="${record_id}">
        <td>${record_id}</td>
        <td>${res.doctor}</td>
        <td>${taskStatus}</td>
      </tr>`;
      var table = document.getElementById('records');
      table.innerHTML += html;
    }


    if (taskStatus === 'Успешно' || taskStatus === 'FAILURE') return false;
    setTimeout(function() {
      getStatus(res.record_id);
    }, 2000);
  })
  .catch(err => console.log(err));
}