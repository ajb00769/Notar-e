import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardGreeter } from './dashboard-greeter';

describe('DashboardGreeter', () => {
  let component: DashboardGreeter;
  let fixture: ComponentFixture<DashboardGreeter>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardGreeter]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DashboardGreeter);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
